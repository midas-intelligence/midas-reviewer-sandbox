"""Note storage and the access rules that go with it."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ..models import Note
from ..security import has_role


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_note(
    conn: sqlite3.Connection,
    *,
    owner_id: int,
    title: str,
    body: str = "",
    visibility: str = "private",
) -> Note:
    if visibility not in ("private", "shared", "public"):
        raise ValueError(f"unknown visibility {visibility!r}")
    cur = conn.execute(
        "INSERT INTO notes (owner_id, title, body, visibility, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (owner_id, title, body, visibility, _now(), _now()),
    )
    conn.commit()
    return get_note(conn, cur.lastrowid)


def get_note(conn: sqlite3.Connection, note_id: int) -> Note | None:
    row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    return Note.from_row(row) if row else None


def list_notes(conn: sqlite3.Connection, *, user_id: int, limit: int, offset: int) -> list[Note]:
    """Notes the user owns, plus anything public. Shared notes come through `shares`."""
    rows = conn.execute(
        """
        SELECT * FROM notes
        WHERE owner_id = ?
           OR visibility = 'public'
           OR id IN (SELECT note_id FROM shares WHERE user_id = ?)
        ORDER BY updated_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, user_id, limit, offset),
    ).fetchall()
    return [Note.from_row(r) for r in rows]


def count_notes(conn: sqlite3.Connection, *, user_id: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) AS n FROM notes
        WHERE owner_id = ?
           OR visibility = 'public'
           OR id IN (SELECT note_id FROM shares WHERE user_id = ?)
        """,
        (user_id, user_id),
    ).fetchone()
    return int(row["n"])


def update_note(
    conn: sqlite3.Connection,
    *,
    note_id: int,
    user_id: int,
    title: str | None = None,
    body: str | None = None,
) -> Note | None:
    """Update a note the user may edit. Returns None when the user may not."""
    note = get_note(conn, note_id)
    if note is None or not can_edit(conn, note=note, user_id=user_id):
        return None
    sets, params = [], []
    if title is not None:
        sets.append("title = ?")
        params.append(title)
    if body is not None:
        sets.append("body = ?")
        params.append(body)
    if not sets:
        return note
    sets.append("updated_at = ?")
    params.extend([_now(), note_id])
    conn.execute(f"UPDATE notes SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    return get_note(conn, note_id)


def delete_note(conn: sqlite3.Connection, *, note_id: int, user_id: int) -> bool:
    note = get_note(conn, note_id)
    if note is None or note.owner_id != user_id:
        return False
    conn.execute("DELETE FROM shares WHERE note_id = ?", (note_id,))
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    return True


def share_role(conn: sqlite3.Connection, *, note_id: int, user_id: int) -> str | None:
    row = conn.execute(
        "SELECT role FROM shares WHERE note_id = ? AND user_id = ?", (note_id, user_id)
    ).fetchone()
    return row["role"] if row else None


def can_read(conn: sqlite3.Connection, *, note: Note, user_id: int) -> bool:
    if note.owner_id == user_id or note.visibility == "public":
        return True
    role = share_role(conn, note_id=note.id, user_id=user_id)
    return role is not None and has_role(role, "viewer")


def can_edit(conn: sqlite3.Connection, *, note: Note, user_id: int) -> bool:
    if note.owner_id == user_id:
        return True
    role = share_role(conn, note_id=note.id, user_id=user_id)
    return role is not None and has_role(role, "editor")


def share_note(conn: sqlite3.Connection, *, note_id: int, owner_id: int, user_id: int, role: str) -> bool:
    """Give another user access. Only the owner may share."""
    note = get_note(conn, note_id)
    if note is None or note.owner_id != owner_id:
        return False
    if role not in ("viewer", "editor"):
        raise ValueError(f"cannot share with role {role!r}")
    conn.execute(
        "INSERT INTO shares (note_id, user_id, role) VALUES (?, ?, ?)"
        " ON CONFLICT(note_id, user_id) DO UPDATE SET role = excluded.role",
        (note_id, user_id, role),
    )
    conn.execute(
        "UPDATE notes SET visibility = 'shared', updated_at = ? WHERE id = ? AND visibility = 'private'",
        (_now(), note_id),
    )
    conn.commit()
    return True
