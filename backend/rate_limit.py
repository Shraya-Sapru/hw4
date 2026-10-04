"""Login lockout after repeated failed attempts.

Keeps a simple in-memory counter of failed login attempts per email. After
MAX_FAILED_ATTEMPTS in a row for the same email, further attempts are
rejected with a 429 for LOCKOUT_SECONDS, regardless of whether the
password submitted next would've been correct.

This is intentionally in-memory, not a database table — the project's
constraint is that the backend only ever writes to the `users` table, and
a login-attempt counter isn't account data, it's transient rate-limit
bookkeeping. The trade-off: this resets if the backend process restarts,
and wouldn't be shared across multiple server instances. For a single
local dev server (or a small deployment with one worker process), that's
a reasonable trade-off; a real multi-instance deployment would want this
in something shared like Redis instead.
"""

import time

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 5 * 60  # 5 minutes

_failed_attempts: dict[str, int] = {}
_locked_until: dict[str, float] = {}


def seconds_until_unlocked(email: str) -> float | None:
    """None if not locked. Otherwise, how many seconds remain."""
    until = _locked_until.get(email)
    if until is None:
        return None

    remaining = until - time.time()
    if remaining <= 0:
        # Lockout has expired — clear it so this email starts fresh.
        _locked_until.pop(email, None)
        _failed_attempts.pop(email, None)
        return None

    return remaining


def record_failed_attempt(email: str) -> None:
    count = _failed_attempts.get(email, 0) + 1
    _failed_attempts[email] = count
    if count >= MAX_FAILED_ATTEMPTS:
        _locked_until[email] = time.time() + LOCKOUT_SECONDS


def record_successful_login(email: str) -> None:
    _failed_attempts.pop(email, None)
    _locked_until.pop(email, None)
