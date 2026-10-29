"""SQLite access.

Connections are opened per request by the caller and closed with `closing()`.
"""
from __future__ import annotations

import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL DEFAULT 'member',
    created_at    TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id   INTEGER NOT NULL REFERENCES users(id),
    title      TEXT    NOT NULL,
    body       TEXT    NOT NULL DEFAULT '',
    visibility TEXT    NOT NULL DEFAULT 'private',
    created_at TEXT    NOT NULL,
    updated_at TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS shares (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    role    TEXT    NOT NULL DEFAULT 'viewer',
    PRIMARY KEY (note_id, user_id)
);

CREATE INDEX IF NOT EXISTS notes_owner_idx ON notes (owner_id);
"""


def connect(database_url: str) -> sqlite3.Connection:
    """Open a connection. `sqlite:///path` and `sqlite://:memory:` are both accepted."""
    path = database_url.split("sqlite://", 1)[-1].removeprefix("/") or ":memory:"
    if path == ":memory:":
        conn = sqlite3.connect(":memory:")
    else:
        conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
