"""Application entry point."""
from __future__ import annotations

import sqlite3

from fastapi import FastAPI

from .config import Settings, load_settings
from .db import connect, init_db
from .routers import notes, users

app = FastAPI(title="Notes sandbox", version="0.4.0")

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


app.include_router(users.router)
app.include_router(notes.router)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "version": app.version}
