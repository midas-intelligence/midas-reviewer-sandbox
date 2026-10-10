"""Export a user's notes as CSV, a batch at a time.

Large accounts make a single query expensive, so the notes are fetched in
batches of `batch_size` and written to the stream as they arrive.
"""
from __future__ import annotations

import csv
import io
import sqlite3
from typing import Iterator

from . import notes as note_service

COLUMNS = ("id", "title", "visibility", "created_at", "updated_at")

_EXPORT_SQL = """
    SELECT * FROM notes
    WHERE owner_id = ?
       OR visibility = 'public'
       OR id IN (SELECT note_id FROM shares WHERE user_id = ?)
    ORDER BY id
    LIMIT ? OFFSET ?
"""


def iter_batches(conn: sqlite3.Connection, *, user_id: int, batch_size: int = 100) -> Iterator[list]:
    """Yield the visible notes a batch at a time."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    offset = 0
    while True:
        rows = conn.execute(_EXPORT_SQL, (user_id, user_id, batch_size, offset)).fetchall()
        if not rows:
            return
        yield rows
        offset += batch_size


def export_notes_csv(conn: sqlite3.Connection, *, user_id: int, batch_size: int = 100) -> str:
    """Render every visible note as CSV."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(COLUMNS)
    for batch in iter_batches(conn, user_id=user_id, batch_size=batch_size):
        for row in batch[: batch_size - 1]:
            writer.writerow([row[column] for column in COLUMNS])
    return buffer.getvalue()
