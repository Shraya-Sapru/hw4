"""Sign up and log in endpoints, plus identifying the current user from
their session token.

Only `signup` ever writes to the database, and it only ever writes to
the `users` table via one parameterized INSERT. `login` and
`get_current_user` only read.
"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

from models import AuthenticatedUser
from rate_limit import (
    record_failed_attempt,
    record_successful_login,
    seconds_until_unlocked,
)
from security import hash_password, verify_password
from session import create_session_token, decode_session_token

BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR.parent / "data" / "campus_customs.db"

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_read_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def get_write_connection() -> sqlite3.Connection:
    """A normal (writable) connection. Only ever used here for one INSERT
    into `users` — never used to touch any other table."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# --- request/response models ------------------------------------------------

class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class PublicUser(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: PublicUser


# --- endpoints ---------------------------------------------------------------

@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(body: SignupRequest):
    email = body.email.lower()

    read_conn = get_read_connection()
    try:
        existing = read_conn.execute(
            "SELECT id FROM users WHERE lower(email) = ?", (email,)
        ).fetchone()
    finally:
        read_conn.close()

    if existing is not None:
        # Deliberately specific here (unlike login) — a duplicate-email
        # check isn't a security-sensitive distinction the way "which
        # part of your login was wrong" is.
        raise HTTPException(status_code=409, detail="An account with that email already exists.")

    password_hash = hash_password(body.password)
    full_name = f"{body.first_name.strip()} {body.last_name.strip()}"

    write_conn = get_write_connection()
    try:
        cursor = write_conn.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (full_name, email, password_hash, body.first_name.strip(), body.last_name.strip()),
        )
        write_conn.commit()
        user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        # Backstop in case of a race between the check above and this insert.
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    finally:
        write_conn.close()

    token = create_session_token(user_id, email)
    return AuthResponse(
        access_token=token,
        user=PublicUser(
            id=user_id,
            first_name=body.first_name.strip(),
            last_name=body.last_name.strip(),
            email=email,
        ),
    )


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    email = body.email.lower()

    locked_seconds = seconds_until_unlocked(email)
    if locked_seconds is not None:
        wait_minutes = max(1, int(locked_seconds // 60) + 1)
        raise HTTPException(
            status_code=429,
            detail=f"Too many failed login attempts. Try again in about {wait_minutes} minute(s).",
        )

    conn = get_read_connection()
    try:
        row = conn.execute(
            "SELECT id, email, password_hash, first_name, last_name FROM users WHERE lower(email) = ?",
            (email,),
        ).fetchone()
    finally:
        conn.close()

    # Same generic error whether the email doesn't exist or the password
    # is wrong, so a caller can't use this endpoint to discover which
    # emails have accounts.
    generic_error = HTTPException(status_code=401, detail="Incorrect email or password.")

    if row is None:
        record_failed_attempt(email)
        raise generic_error

    if not verify_password(body.password, row["password_hash"]):
        record_failed_attempt(email)
        raise generic_error

    record_successful_login(email)
    token = create_session_token(row["id"], row["email"])
    return AuthResponse(
        access_token=token,
        user=PublicUser(
            id=row["id"],
            first_name=row["first_name"] or "",
            last_name=row["last_name"] or "",
            email=row["email"],
        ),
    )


def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser | None:
    """Who's making this request, based on their session token — never
    based on anything else the request body claims. Returns None for a
    guest (no token, an invalid/expired one, or a deleted account), never
    raises — most routes that use this should work for guests too, just
    without the personalization/persistence that comes with being logged in.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_session_token(token)
    if payload is None:
        return None

    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        return None

    conn = get_read_connection()
    try:
        row = conn.execute(
            "SELECT id, first_name, last_name, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return AuthenticatedUser(
        id=row["id"],
        first_name=row["first_name"] or "",
        last_name=row["last_name"] or "",
        email=row["email"],
    )
