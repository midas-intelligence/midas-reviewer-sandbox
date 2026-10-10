"""Row shapes returned by the service layer."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    role: str
    created_at: str


@dataclass(frozen=True)
class Note:
    id: int
    owner_id: int
    title: str
    body: str
    visibility: str
    created_at: str
    updated_at: str

    @staticmethod
    def from_row(row) -> "Note":
        return Note(
            id=row["id"],
            owner_id=row["owner_id"],
            title=row["title"],
            body=row["body"],
            visibility=row["visibility"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass(frozen=True)
class Share:
    note_id: int
    user_id: int
    role: str
