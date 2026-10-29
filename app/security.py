"""Password hashing, bearer tokens and the role ladder."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

# Ordered from least to most privileged.
ROLES = ("viewer", "editor", "owner")
PBKDF2_ROUNDS = 120_000


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"pbkdf2${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, rounds, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "pbkdf2":
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(rounds))
    return hmac.compare_digest(digest.hex(), digest_hex)


def role_rank(role: str) -> int:
    """Position on the ladder, or -1 for a role we do not know."""
    try:
        return ROLES.index(role)
    except ValueError:
        return -1


def has_role(actual: str, required: str) -> bool:
    """True when `actual` sits at or above `required` on the ladder."""
    return role_rank(actual) >= role_rank(required)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def issue_token(secret: str, *, user_id: int, ttl_seconds: int) -> str:
    payload = json.dumps({"sub": user_id, "exp": int(time.time()) + ttl_seconds}, separators=(",", ":"))
    body = _b64(payload.encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    return f"{body}.{_b64(signature)}"


def read_token(secret: str, token: str) -> dict | None:
    """Return the payload, or None when the token is malformed, forged or expired."""
    if not token or token.count(".") != 1:
        return None
    body, signature = token.split(".")
    try:
        expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
    except UnicodeEncodeError:
        return None
    try:
        given = _unb64(signature)
    except (ValueError, TypeError):
        return None
    if not hmac.compare_digest(expected, given):
        return None
    try:
        payload = json.loads(_unb64(body))
    except (ValueError, TypeError):
        return None
    if not isinstance(payload, dict) or payload.get("exp", 0) < time.time():
        return None
    return payload
