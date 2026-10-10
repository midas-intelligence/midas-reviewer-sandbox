"""Tags: a per-user label that can be attached to any note the user may edit."""
from __future__ import annotations

import sqlite3

from . import notes as note_service

MAX_NAME_LENGTH = 32


def _normalise(name: str) -> str:
    name = name.strip().lower()
    if not name:
        raise ValueError("a tag needs a name")
    if len(name) > MAX_NAME_LENGTH:
        raise ValueError(f"a tag name is at most {MAX_NAME_LENGTH} characters")
    return name


def _ensure_tag(conn: sqlite3.Connection, *, owner_id: int, name: str) -> int:
    conn.execute(
        "INSERT INTO tags (owner_id, name) VALUES (?, ?) ON CONFLICT(owner_id, name) DO NOTHING",
        (owner_id, name),
    )
    row = conn.execute(
        "SELECT id FROM tags WHERE owner_id = ? AND name = ?", (owner_id, name)
    ).fetchone()
    return int(row["id"])


def add_tag(conn: sqlite3.Connection, *, note_id: int, user_id: int, name: str) -> bool:
    """Attach a tag to a note the user may edit. Returns False when they may not."""
    note = note_service.get_note(conn, note_id)
    if note is None or not note_service.can_edit(conn, note=note, user_id=user_id):
        return False
    tag_id = _ensure_tag(conn, owner_id=user_id, name=_normalise(name))
    conn.execute(
        "INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?) ON CONFLICT DO NOTHING",
        (note_id, tag_id),
    )
    conn.commit()
    return True


def remove_tag(conn: sqlite3.Connection, *, note_id: int, user_id: int, name: str) -> bool:
    note = note_service.get_note(conn, note_id)
    if note is None or not note_service.can_edit(conn, note=note, user_id=user_id):
        return False
    row = conn.execute(
        "SELECT id FROM tags WHERE owner_id = ? AND name = ?", (user_id, _normalise(name))
    ).fetchone()
    if row is None:
        return False
    conn.execute("DELETE FROM note_tags WHERE note_id = ? AND tag_id = ?", (note_id, row["id"]))
    conn.commit()
    return True


def tags_for_note(conn: sqlite3.Connection, *, note_id: int) -> list[str]:
    rows = conn.execute(
        "SELECT t.name FROM tags t JOIN note_tags nt ON nt.tag_id = t.id"
        " WHERE nt.note_id = ? ORDER BY t.name",
        (note_id,),
    ).fetchall()
    return [r["name"] for r in rows]


def notes_with_tag(conn: sqlite3.Connection, *, user_id: int, name: str) -> list[int]:
    """The ids of the user's visible notes carrying a tag."""
    rows = conn.execute(
        """
        SELECT n.id FROM notes n
        JOIN note_tags nt ON nt.note_id = n.id
        JOIN tags t ON t.id = nt.tag_id
        WHERE t.owner_id = ? AND t.name = ?
          AND (n.owner_id = ? OR n.visibility = 'public'
               OR n.id IN (SELECT note_id FROM shares WHERE user_id = ?))
        ORDER BY n.id
        """,
        (user_id, _normalise(name), user_id, user_id),
    ).fetchall()
    return [r["id"] for r in rows]
