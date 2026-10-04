"""Append-only audit trail of agent activity — output/audit_trail.json.

Every entry is one of two kinds, sharing the same shape:
  - a tool call ("event": "tool_call") — which tool ran, a short safe
    summary of its arguments and result.
  - a run summary ("event": "run_summary"), written once per chat
    message handled — why the run stopped (completed normally, hit a
    usage limit, the message was too long, or a model/API error), plus
    how many model requests and tool calls that run actually used.

Safety: argument/result values are truncated and recursively summarized
(see summarize_value) before ever being written — no full message text,
no long free-text fields, and any field whose name looks sensitive
(password, hash, token, key, secret, authorization) is redacted outright
as a defense-in-depth measure, even though none of the current tools'
arguments or results actually contain anything like that.

Concurrency & durability: a cross-process file lock (via `filelock`)
guards every read-modify-write cycle, and each write goes to a temp file
that's then atomically renamed over the real one — so two requests
appending at once can't corrupt or race on the file, a crash mid-write
can't leave a half-written file behind, and a server restart never
touches what's already on disk. The file is never truncated or
rewritten from scratch; every write starts by reading whatever's already
there and only ever adds to it.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from filelock import FileLock

logger = logging.getLogger("campus_customs.audit")

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
AUDIT_PATH = PROJECT_ROOT / "output" / "audit_trail.json"
LOCK_PATH = AUDIT_PATH.parent / "audit_trail.json.lock"

MAX_STRING_LENGTH = 60
MAX_LIST_ITEMS = 3

_SENSITIVE_KEY_MARKERS = ("password", "hash", "token", "key", "secret", "authorization")

_lock = FileLock(str(LOCK_PATH))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def summarize_value(value: Any, _depth: int = 0) -> Any:
    """Recursively turns a value into something short and safe to log:
    long strings get truncated, long lists get capped (with a count of
    what was left out), and any dict key that looks sensitive gets
    redacted outright rather than summarized."""
    if _depth > 4:
        return "…"

    if isinstance(value, str):
        if len(value) > MAX_STRING_LENGTH:
            return value[:MAX_STRING_LENGTH] + "…"
        return value

    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, val in value.items():
            if any(marker in key.lower() for marker in _SENSITIVE_KEY_MARKERS):
                out[key] = "«redacted»"
            else:
                out[key] = summarize_value(val, _depth + 1)
        return out

    if isinstance(value, (list, tuple)):
        items = [summarize_value(v, _depth + 1) for v in value[:MAX_LIST_ITEMS]]
        remaining = len(value) - len(items)
        if remaining > 0:
            items.append(f"…(+{remaining} more)")
        return items

    return value


def _read_entries() -> list[dict]:
    """Returns the entries currently on disk, or [] if the file doesn't
    exist yet. Must only be called while holding _lock."""
    if not AUDIT_PATH.exists():
        return []
    text = AUDIT_PATH.read_text(encoding="utf-8")
    if not text.strip():
        return []
    return json.loads(text)


def _append(entry: dict) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        try:
            entries = _read_entries()
        except (json.JSONDecodeError, OSError):
            # The file exists but isn't valid JSON right now. Refusing to
            # write rather than overwriting it with a fresh, shorter list
            # is the one choice that can never destroy old entries — the
            # worst outcome here is a dropped log line, never lost history.
            logger.warning("audit_trail.json is unreadable; skipping this entry rather than overwriting it")
            return

        entries.append(entry)

        tmp_path = AUDIT_PATH.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        os.replace(tmp_path, AUDIT_PATH)  # atomic on both Windows and POSIX


def log_tool_call(conversation_id: str, tool_name: str, args: dict, result: Any) -> None:
    entry = {
        "timestamp": _now_iso(),
        "conversation_id": conversation_id,
        "event": "tool_call",
        "tool_name": tool_name,
        "summary": {
            "args": summarize_value(args),
            "result": summarize_value(result),
        },
        "stop_reason": None,
    }
    try:
        _append(entry)
    except Exception:
        # A logging failure should never take down the actual feature.
        logger.warning("Failed to append tool-call audit entry", exc_info=True)


def log_run_summary(
    conversation_id: str,
    stop_reason: str,
    requests: int | None = None,
    tool_calls: int | None = None,
) -> None:
    entry = {
        "timestamp": _now_iso(),
        "conversation_id": conversation_id,
        "event": "run_summary",
        "tool_name": None,
        "summary": {"requests": requests, "tool_calls": tool_calls},
        "stop_reason": stop_reason,
    }
    try:
        _append(entry)
    except Exception:
        logger.warning("Failed to append run-summary audit entry", exc_info=True)
