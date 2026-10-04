"""Builds the Campus Customs chat agent.

The agent talks to the model through Portkey (not directly to OpenAI): we
hand PydanticAI an OpenAI-compatible client whose base_url points at
Portkey, with the actual provider named via a header. The API key comes
from PORTKEY_API_KEY in the project's .env file — never hardcoded here.
"""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import AgentRunError, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    SystemPromptPart,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

from audit import log_run_summary
from chat_history import get_recent_history, save_message
from conversations import get_history, new_conversation_id, save_history
from deps import ChatDeps
from models import AuthenticatedUser, ChatReply, ChatResponse, CustomerInfo
from tools import TOOLS

logger = logging.getLogger("campus_customs.agent")

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"

load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = "gpt-5.6-terra"
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")

# --- Per-message limits (Problem 12) -----------------------------------
#
# These bound how much work a single /api/chat call can do, so a
# confused loop (or a malicious prompt trying to run up cost) can't spin
# forever or hammer the catalogue database unboundedly.
#
# MAX_MODEL_REQUESTS / MAX_TOOL_CALLS feed pydantic-ai's own UsageLimits,
# which stops the run and raises UsageLimitExceeded once either is hit —
# verified directly against the installed pydantic-ai's UsageLimits
# signature and UsageLimitExceeded exception rather than assumed from
# memory. MAX_MESSAGE_LENGTH and MAX_HISTORY_MESSAGES are checked here,
# before the run even starts.
MAX_MODEL_REQUESTS = 8
MAX_TOOL_CALLS = 8
USAGE_LIMITS = UsageLimits(request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS)

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_MESSAGES = 20

FRIENDLY_LIMIT_REPLY = ChatReply(
    message=(
        "That's a lot for me to process in one go! Could you break that into a "
        "shorter message, or ask me one thing at a time?"
    ),
)

_openai_client = AsyncOpenAI(
    api_key=os.environ["PORTKEY_API_KEY"],
    base_url="https://api.portkey.ai/v1",
    default_headers={"x-portkey-provider": "openai"},
)

_model = OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=_openai_client))

agent = Agent(
    _model,
    deps_type=ChatDeps,
    output_type=ChatReply,
    system_prompt=SYSTEM_PROMPT,
    tools=TOOLS,
)


@agent.system_prompt
def customer_context(ctx: RunContext[ChatDeps]) -> str:
    """Appended to the static system prompt at run-time — who the agent is
    talking to, and what page they're on. This is the only way the model
    actually learns about ctx.deps; tools can read ctx.deps directly, but
    the model itself only sees whatever text we put here."""
    lines: list[str] = []

    if ctx.deps.user is not None:
        lines.append(
            f"You are talking with {ctx.deps.user.first_name} {ctx.deps.user.last_name}, "
            f"a logged-in customer (email: {ctx.deps.user.email}). Feel free to greet them "
            "by first name, especially at the start of a conversation."
        )
    else:
        lines.append(
            "This visitor is a guest — not logged in. Don't address them by name, "
            "and don't assume you know anything about them."
        )

    if ctx.deps.product_context_id:
        lines.append(
            f"They are currently viewing the product page for product_id "
            f"'{ctx.deps.product_context_id}'. If they say things like \"this\" or \"it\" "
            "without naming an item, they most likely mean this product."
        )

    return "\n".join(lines)


FALLBACK_REPLY = ChatReply(
    message=(
        "Sorry, I'm having trouble answering that right now. "
        "Please try rephrasing, or try again in a moment."
    ),
)


class _DepsOnly:
    """A minimal stand-in for RunContext — just enough for customer_context()
    below, which only ever reads `.deps`. Used to render the dynamic system
    prompt by hand for seeded history (see _history_messages_to_seed)."""

    def __init__(self, deps: ChatDeps) -> None:
        self.deps = deps


def _history_messages_to_seed(user_id: int, deps: ChatDeps) -> list[ModelMessage]:
    """Turns this customer's saved chat_messages rows into PydanticAI
    message history, so a brand-new conversation (no conversation_id yet)
    still has their past conversations to continue from. This only
    reconstructs the text of each turn, not the exact tool calls that
    produced it — enough for the model to have real continuity, even
    though it isn't a byte-for-byte replay of the original run.

    Important: PydanticAI only generates system-prompt messages when the
    message_history it's given is completely empty — it assumes a
    non-empty history already has them from an earlier real run. A
    seeded history built here never went through a real run, so without
    this, every guardrail and bit of context in prompt.md would silently
    vanish for the rest of the conversation. So the static prompt and the
    customer_context() dynamic prompt are rendered by hand here and
    prepended, exactly mirroring what a real first turn would have
    produced.
    """
    seed: list[ModelMessage] = [
        ModelRequest(
            parts=[
                SystemPromptPart(content=SYSTEM_PROMPT),
                SystemPromptPart(content=customer_context(_DepsOnly(deps))),
            ]
        )
    ]
    for entry in get_recent_history(user_id):
        if entry.role == "user":
            seed.append(ModelRequest(parts=[UserPromptPart(content=entry.content)]))
        elif entry.role == "assistant":
            seed.append(ModelResponse(parts=[TextPart(content=entry.content)]))
    return seed


async def run_agent(
    message: str,
    conversation_id: str | None,
    user: AuthenticatedUser | None,
    page_product_id: str | None,
) -> ChatResponse:
    """Runs the agent with the conversation's prior message history (so it
    remembers earlier turns — e.g. which product was being discussed), and
    never lets a model/API failure turn into a 500: a content filter
    rejection, a rate limit, or a flaky upstream request all just fall
    back to a friendly in-character message instead.

    If `user` is logged in and this is a brand-new conversation (no
    conversation_id yet), their saved chat history is loaded to seed it,
    so they can pick up an earlier conversation across visits. Guests
    never have anything saved, and nothing is ever saved for them.
    """
    active_id = conversation_id or new_conversation_id()

    deps = ChatDeps(
        user=(
            CustomerInfo(
                first_name=user.first_name, last_name=user.last_name, email=user.email
            )
            if user is not None
            else None
        ),
        product_context_id=page_product_id,
        conversation_id=active_id,
    )

    if len(message) > MAX_MESSAGE_LENGTH:
        log_run_summary(active_id, "message_too_long")
        return ChatResponse(**FRIENDLY_LIMIT_REPLY.model_dump(), conversation_id=active_id)

    if conversation_id is not None:
        history = get_history(conversation_id)
    elif user is not None:
        history = _history_messages_to_seed(user.id, deps)
    else:
        history = []

    # Cap how much history is replayed to the model. history[0] may carry
    # the SystemPromptPart(s) that stand in for the system prompt (see
    # _history_messages_to_seed) — dropping it would silently lose every
    # guardrail in prompt.md for the rest of the conversation, so it's
    # always kept regardless of how the rest is trimmed.
    if len(history) > MAX_HISTORY_MESSAGES:
        history = [history[0], *history[-(MAX_HISTORY_MESSAGES - 1) :]]

    try:
        result = await agent.run(
            message, message_history=history, deps=deps, usage_limits=USAGE_LIMITS
        )
    except UsageLimitExceeded:
        logger.info("Agent run hit a usage limit for conversation %s", active_id)
        log_run_summary(active_id, "usage_limit_exceeded")
        return ChatResponse(**FRIENDLY_LIMIT_REPLY.model_dump(), conversation_id=active_id)
    except AgentRunError:
        logger.warning("Agent run failed, returning fallback reply", exc_info=True)
        log_run_summary(active_id, "model_error")
        return ChatResponse(**FALLBACK_REPLY.model_dump(), conversation_id=active_id)

    usage = result.usage
    log_run_summary(
        active_id, "completed", requests=usage.requests, tool_calls=usage.tool_calls
    )

    save_history(active_id, result.all_messages())

    if user is not None:
        save_message(user.id, "user", message)
        save_message(user.id, "assistant", result.output.message, products=result.output.products or None)

    return ChatResponse(**result.output.model_dump(), conversation_id=active_id)
