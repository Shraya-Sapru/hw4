"""Password hashing utilities.

Password hashes in the `users` table look like this:

    pbkdf2_sha256$<salt>$<hex digest>

That's the scheme the three seed accounts (Test User, Ada Lovelace,
Tauhid Zaman) were already stored with — PBKDF2-HMAC-SHA256, a `$`-joined
string of the algorithm name, a salt, and the resulting digest as hex.

PBKDF2's iteration count isn't embedded in this hash string, so it
couldn't be read off directly — but it could be confirmed by testing a
known seed login (test@campuscustoms.yale.edu / "password") against a
range of common iteration counts. 120,000 iterations reproduces that
account's stored hash exactly, so that's the iteration count used here
for every password this app hashes or verifies, matching whatever
script originally seeded the `users` table.

The other two seed accounts (Ada Lovelace, Tauhid Zaman) use this same
hash format, so they're assumed to share the same iteration count, but
their actual plaintext passwords aren't known — only the test account's
password was confirmed.
"""

import hashlib
import hmac
import secrets

ALGORITHM_NAME = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 120_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return f"{ALGORITHM_NAME}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    parts = stored_hash.split("$")
    if len(parts) != 3 or parts[0] != ALGORITHM_NAME:
        return False

    _, salt, expected_digest = parts
    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()

    # constant-time comparison so a mismatch can't be timed to leak
    # information about how much of the digest matched
    return hmac.compare_digest(candidate_digest, expected_digest)
