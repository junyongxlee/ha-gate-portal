"""PIN hashing and verification."""

from __future__ import annotations

import hashlib
import hmac
import secrets

PIN_ITERATIONS = 100_000


def hash_pin(pin: str) -> str:
    """Hash a PIN for storage."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt.encode("utf-8"),
        PIN_ITERATIONS,
    ).hex()
    return f"{salt}${digest}"


def verify_pin(pin: str, stored_hash: str) -> bool:
    """Verify a PIN against a stored hash."""
    try:
        salt, expected = stored_hash.split("$", 1)
    except ValueError:
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt.encode("utf-8"),
        PIN_ITERATIONS,
    ).hex()
    return hmac.compare_digest(digest, expected)
