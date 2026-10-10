"""User registration and lookup."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ..models import User
from ..security import hash_password, verify_password


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _as_user(row: sqlite3.Row | None) -> User | None:
    if row is None:
        return None
    return User(id=row["id"], email=row["email"], role=row["role"], created_at=row["created_at"])


def register(conn: sqlite3.Connection, *, email: str, password: str, role: str = "member") -> User:
    """Create a user. Raises sqlite3.IntegrityError when the email is taken."""
    cur = conn.execute(
        "INSERT INTO users (email, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
        (email.strip().lower(), hash_password(password), role, _now()),
    )
    conn.commit()
    return _as_user(conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone())


def find_by_email(conn: sqlite3.Connection, email: str) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    return _as_user(row)


def find_by_id(conn: sqlite3.Connection, user_id: int) -> User | None:
    return _as_user(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def authenticate(conn: sqlite3.Connection, *, email: str, password: str) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return _as_user(row)
