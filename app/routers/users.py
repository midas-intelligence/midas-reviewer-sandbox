"""Registration, login and the current-user endpoint."""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..security import issue_token, read_token
from ..services import users as user_service

router = APIRouter(prefix="/users", tags=["users"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def current_user(conn, authorization: str | None, secret: str):
    """Resolve a bearer token to a user, or raise 401."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    payload = read_token(secret, authorization.removeprefix("Bearer ").strip())
    if payload is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token")
    user = user_service.find_by_id(conn, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "unknown user")
    return user


@router.post("/register", status_code=201)
def register(body: RegisterRequest, conn: sqlite3.Connection = Depends(lambda: None)):
    if len(body.password) < 10:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "password must be at least 10 characters")
    try:
        user = user_service.register(conn, email=body.email, password=body.password)
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "email already registered")
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login")
def login(body: LoginRequest, conn: sqlite3.Connection = Depends(lambda: None)):
    user = user_service.authenticate(conn, email=body.email, password=body.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    from ..main import settings_for

    return {"token": issue_token(settings_for().secret_key, user_id=user.id,
                                 ttl_seconds=settings_for().token_ttl_seconds),
            "user": {"id": user.id, "email": user.email, "role": user.role}}
