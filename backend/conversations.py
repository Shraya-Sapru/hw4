"""In-memory chat history store, keyed by conversation_id.

Each call to /api/chat was previously stateless — every message ran as a
brand-new conversation, with no memory of anything said earlier in the
same chat. This module fixes that by keeping each conversation's message
history (in PydanticAI's own message format, so tool calls and structured
output round-trip correctly) between requests.

Like rate_limit.py, this is deliberately in-memory rather than a database
table: it's transient session state, not account data, and this backend
only ever writes to `users`. The trade-off is the same one documented
there — history resets if the backend restarts, and wouldn't be shared
across multiple server processes. Fine for a single local dev server; a
real deployment would want this in something shared instead.
"""

import uuid

from pydantic_ai.messages import ModelMessage

_histories: dict[str, list[ModelMessage]] = {}


def new_conversation_id() -> str:
    return uuid.uuid4().hex


def get_history(conversation_id: str | None) -> list[ModelMessage]:
    if conversation_id is None:
        return []
    return _histories.get(conversation_id, [])


def save_history(conversation_id: str, messages: list[ModelMessage]) -> None:
    _histories[conversation_id] = messages
