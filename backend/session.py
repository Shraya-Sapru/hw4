"""Login sessions, as a signed token — no session table.

The assignment only allows this backend to write to the `users` table,
so sessions can't be stored server-side in their own table. Instead we
hand the frontend a JWT (JSON Web Token) when login/signup succeeds:

  - The token's payload holds the user's id, email, and an expiry time.
  - It's signed with HMAC-SHA256 using SESSION_SECRET_KEY, a secret kept
    only in the project's .env file (never sent to the frontend, never
    committed to the repo).
  - Because it's *signed*, the server can tell whether a token it's
    handed back later was actually issued by this server and hasn't
    expired, without looking anything up in a database — the token
    carries its own proof.
  - The frontend's job is just to hold on to the token (we use
    localStorage) and send it back on future requests, typically as
    `Authorization: Bearer <token>`. There's no server-side "log out"
    needed for a stateless token — the frontend deleting its copy of
    the token is what "logging out" means here.

This module only encodes/decodes that token; it doesn't touch the
database at all.
"""

import os
import time
from pathlib import Path

import jwt
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SESSION_SECRET_KEY = os.environ["SESSION_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME_SECONDS = 60 * 60 * 24 * 7  # 7 days


def create_session_token(user_id: int, email: str) -> str:
    now = int(time.time())
    payload = {
        # The JWT spec (RFC 7519) requires "sub" to be a string — PyJWT
        # enforces this on decode, so it has to be stringified here too,
        # even though it's really our integer user id.
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + TOKEN_LIFETIME_SECONDS,
    }
    return jwt.encode(payload, SESSION_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_session_token(token: str) -> dict | None:
    """Returns the payload if the token is valid and not expired, else None.
    "sub" comes back as the string it was encoded as — callers that need
    the numeric user id back should int() it themselves."""
    try:
        return jwt.decode(token, SESSION_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
