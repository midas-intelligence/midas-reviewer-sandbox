"""Note CRUD, listing and sharing."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, status
from pydantic import BaseModel

from ..services import notes as note_service
from .users import current_user

router = APIRouter(prefix="/notes", tags=["notes"])


class NoteRequest(BaseModel):
    title: str
    body: str = ""
    visibility: str = "private"


class NotePatch(BaseModel):
    title: str | None = None
    body: str | None = None


class ShareRequest(BaseModel):
    user_id: int
    role: str = "viewer"


def _conn():
    from ..main import connection

    return connection()


def _user(conn=Depends(_conn), authorization: str | None = Header(default=None)):
    from ..main import settings_for

    return current_user(conn, authorization, settings_for().secret_key)


@router.get("")
def list_notes(
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conn: sqlite3.Connection = Depends(_conn),
    user=Depends(_user),
):
    items = note_service.list_notes(conn, user_id=user.id, limit=limit, offset=offset)
    return {
        "items": [n.__dict__ for n in items],
        "total": note_service.count_notes(conn, user_id=user.id),
        "limit": limit,
        "offset": offset,
    }


@router.post("", status_code=201)
def create_note(body: NoteRequest, conn: sqlite3.Connection = Depends(_conn), user=Depends(_user)):
    note = note_service.create_note(
        conn, owner_id=user.id, title=body.title, body=body.body, visibility=body.visibility
    )
    return note.__dict__


@router.get("/{note_id}")
def get_note(note_id: int, conn: sqlite3.Connection = Depends(_conn), user=Depends(_user)):
    note = note_service.get_note(conn, note_id)
    if note is None or not note_service.can_read(conn, note=note, user_id=user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return note.__dict__


@router.patch("/{note_id}")
def patch_note(
    note_id: int, body: NotePatch, conn: sqlite3.Connection = Depends(_conn), user=Depends(_user)
):
    note = note_service.get_note(conn, note_id)
    if note is None or not note_service.can_read(conn, note=note, user_id=user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    updated = note_service.update_note(
        conn, note_id=note_id, user_id=user.id, title=body.title, body=body.body
    )
    if updated is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "you may not edit this note")
    return updated.__dict__


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, conn: sqlite3.Connection = Depends(_conn), user=Depends(_user)):
    if not note_service.delete_note(conn, note_id=note_id, user_id=user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return None


@router.post("/{note_id}/shares", status_code=201)
def share_note(
    note_id: int, body: ShareRequest, conn: sqlite3.Connection = Depends(_conn), user=Depends(_user)
):
    ok = note_service.share_note(
        conn, note_id=note_id, owner_id=user.id, user_id=body.user_id, role=body.role
    )
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return {"note_id": note_id, "user_id": body.user_id, "role": body.role}


@router.get("/{note_id}/shares")
def list_shares(
    note_id: int = Path(ge=1, le=2**63 - 1),  # SQLite rejects ids outside a signed 64-bit range
    conn: sqlite3.Connection = Depends(_conn),
    user=Depends(_user),
):
    shares = note_service.list_shares(conn, note_id=note_id, owner_id=user.id)
    if shares is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "note not found")
    return {"items": [s.__dict__ for s in shares]}
