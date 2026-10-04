"""Saved chat history for logged-in customers.

This reuses the `chat_messages` table that already existed in the seed
database (user_id, role, content, products_json, created_at) — it was
already exactly the shape this needs, so no new table or schema change
was necessary. Nothing here ever touches `users` or any other table.

Guests are never saved: every write here is gated on having a real,
token-verified user id (see backend/auth.py's get_current_user).
"""

import json
import sqlite3
from pathlib import Path

from models import ChatHistoryMessage, ProductCard

BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR.parent / "data" / "campus_customs.db"

HISTORY_LIMIT = 20


def _get_read_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _get_write_connection() -> sqlite3.Connection:
    """A normal (writable) connection. Only ever used here for INSERTs
    into `chat_messages` — never used to touch any other table."""
    return sqlite3.connect(DB_PATH)


def save_message(user_id: int, role: str, content: str, products: list[ProductCard] | None = None) -> None:
    products_json = json.dumps([p.model_dump() for p in products]) if products else None
    conn = _get_write_connection()
    try:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, products_json),
        )
        conn.commit()
    finally:
        conn.close()


def get_recent_history(user_id: int, limit: int = HISTORY_LIMIT) -> list[ChatHistoryMessage]:
    """Most recent messages for this user, oldest first."""
    conn = _get_read_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    finally:
        conn.close()

    rows = list(reversed(rows))  # back to chronological order
    return [
        ChatHistoryMessage(role=row["role"], content=row["content"], created_at=row["created_at"])
        for row in rows
    ]
