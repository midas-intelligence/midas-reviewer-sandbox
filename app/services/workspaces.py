"""Workspaces: named groups of users who share notes.

A workspace member has a role on the same ladder as note sharing, so an
`editor` may change the notes in the workspace and a `viewer` may not.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from ..models import Workspace
from ..security import has_role


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_workspace(conn: sqlite3.Connection, *, owner_id: int, name: str) -> Workspace:
    cur = conn.execute(
        "INSERT INTO workspaces (name, owner_id, created_at) VALUES (?, ?, ?)",
        (name, owner_id, _now()),
    )
    conn.execute(
        "INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, 'owner')",
        (cur.lastrowid, owner_id),
    )
    conn.commit()
    return get_workspace(conn, cur.lastrowid)


def get_workspace(conn: sqlite3.Connection, workspace_id: int) -> Workspace | None:
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    if row is None:
        return None
    return Workspace(
        id=row["id"], name=row["name"], owner_id=row["owner_id"], created_at=row["created_at"]
    )


def add_member(
    conn: sqlite3.Connection, *, workspace_id: int, owner_id: int, user_id: int, role: str
) -> bool:
    """Add or re-role a member. Only the workspace owner may do this."""
    workspace = get_workspace(conn, workspace_id)
    if workspace is None or workspace.owner_id != owner_id:
        return False
    if role not in ("viewer", "editor"):
        raise ValueError(f"cannot add a member as {role!r}")
    conn.execute(
        "INSERT INTO workspace_members (workspace_id, user_id, role) VALUES (?, ?, ?)"
        " ON CONFLICT(workspace_id, user_id) DO UPDATE SET role = excluded.role",
        (workspace_id, user_id, role),
    )
    conn.commit()
    return True


def member_role(conn: sqlite3.Connection, *, workspace_id: int, user_id: int) -> str | None:
    row = conn.execute(
        "SELECT role FROM workspace_members WHERE workspace_id = ? AND user_id = ?",
        (workspace_id, user_id),
    ).fetchone()
    return row["role"] if row else None


def can_read_workspace(conn: sqlite3.Connection, *, workspace_id: int, user_id: int) -> bool:
    """Any member may read the notes in a workspace."""
    role = member_role(conn, workspace_id=workspace_id, user_id=user_id)
    return role is not None and has_role(role, "viewer")


def can_write_workspace(conn: sqlite3.Connection, *, workspace_id: int, user_id: int) -> bool:
    """Members at editor or above may change the notes in a workspace."""
    role = member_role(conn, workspace_id=workspace_id, user_id=user_id)
    return role is not None and has_role(role, "viewer")
