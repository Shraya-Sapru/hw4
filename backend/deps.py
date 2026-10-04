"""The agent's runtime dependencies — who it's talking to, and what page
they're on. Passed in fresh on every /api/chat call; never persisted,
never part of any response model.
"""

from dataclasses import dataclass

from models import CustomerInfo


@dataclass
class ChatDeps:
    user: CustomerInfo | None
    """None for a guest. Never includes a password hash, user id, or any
    other user's data — just enough for the agent to recognize who it's
    talking to."""

    product_context_id: str | None
    """The product_id of the page the customer is currently viewing, if
    any (e.g. they're on /products/<id>). Lets "do you have this in
    pink?" resolve to a real product without them having to name it."""

    conversation_id: str
    """Correlates this run's tool calls in the audit trail (backend/audit.py)
    with the run_summary entry logged once the run finishes."""
