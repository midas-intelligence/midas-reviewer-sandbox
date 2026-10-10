"""Application entry point."""
from __future__ import annotations

import sqlite3

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, cors_origins, load_settings
from .db import connect, init_db
from .routers import notes, users

app = FastAPI(title="Notes sandbox", version="0.5.0")

_settings: Settings | None = None
_conn: sqlite3.Connection | None = None


def settings_for() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def connection() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = connect(settings_for().database_url)
        init_db(_conn)
    return _conn


# The web client is served from its own origin, so the API has to allow it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(cors_origins()),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(notes.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": app.version}


@app.get("/settings")
def public_settings():
    """The handful of settings the web client is allowed to know."""
    settings = settings_for()
    return {
        "page_size": settings.page_size,
        "environment": settings.environment,
        "cors_origins": list(settings.cors_origins),
    }
