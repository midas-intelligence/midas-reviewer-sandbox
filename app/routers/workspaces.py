"""Creating workspaces and managing their members."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..services import workspaces as workspace_service
from .notes import _conn, _user

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceRequest(BaseModel):
    name: str


class MemberRequest(BaseModel):
    user_id: int
    role: str = "viewer"


@router.post("", status_code=201)
def create_workspace(
    body: WorkspaceRequest, conn: sqlite3.Connection = Depends(_conn), user=Depends(_user)
):
    workspace = workspace_service.create_workspace(conn, owner_id=user.id, name=body.name)
    return workspace.__dict__


@router.post("/{workspace_id}/members", status_code=201)
def add_member(
    workspace_id: int,
    body: MemberRequest,
    conn: sqlite3.Connection = Depends(_conn),
    user=Depends(_user),
):
    ok = workspace_service.add_member(
        conn, workspace_id=workspace_id, owner_id=user.id, user_id=body.user_id, role=body.role
    )
    if not ok:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "workspace not found")
    return {"workspace_id": workspace_id, "user_id": body.user_id, "role": body.role}
