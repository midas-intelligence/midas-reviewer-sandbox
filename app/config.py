"""Runtime settings, read from the environment at startup."""
from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigError(RuntimeError):
    """A required setting is missing or malformed."""


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    token_ttl_seconds: int
    page_size: int


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc


def load_settings() -> Settings:
    """Read settings from the environment. Only the secret has no default."""
    secret = os.environ.get("NOTES_SECRET_KEY")
    if not secret:
        raise ConfigError("NOTES_SECRET_KEY must be set")
    return Settings(
        database_url=os.environ.get("NOTES_DATABASE_URL", "sqlite:///./notes.db"),
        secret_key=secret,
        token_ttl_seconds=_int_env("NOTES_TOKEN_TTL", 3600),
        page_size=_int_env("NOTES_PAGE_SIZE", 25),
    )
