"""Service-level tests. These run on the standard library alone."""
from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import load_settings
from app.db import connect, init_db
from app.security import has_role, hash_password, issue_token, read_token, verify_password
from app.services import notes as note_service
from app.services import users as user_service


class SecurityTests(unittest.TestCase):
    def test_password_round_trip(self):
        stored = hash_password("correct horse battery staple")
        self.assertTrue(verify_password("correct horse battery staple", stored))
        self.assertFalse(verify_password("wrong", stored))

    def test_role_ladder(self):
        self.assertTrue(has_role("owner", "editor"))
        self.assertTrue(has_role("editor", "editor"))
        self.assertFalse(has_role("viewer", "editor"))
        self.assertFalse(has_role("member", "viewer"))

    def test_token_round_trip_and_tampering(self):
        token = issue_token("s3cret", user_id=7, ttl_seconds=60)
        self.assertEqual(read_token("s3cret", token)["sub"], 7)
        self.assertIsNone(read_token("other", token))
        self.assertIsNone(read_token("s3cret", token + "x"))


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in ("NOTES_SECRET_KEY", "NOTES_CORS_ORIGINS", "NOTES_ENV")}
        os.environ["NOTES_SECRET_KEY"] = "test-secret"

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_origins_are_split_on_commas(self):
        os.environ["NOTES_CORS_ORIGINS"] = "https://app.example.com, https://admin.example.com"
        self.assertEqual(load_settings().cors_origins,
                         ("https://app.example.com", "https://admin.example.com"))

    def test_origin_defaults_to_any(self):
        os.environ.pop("NOTES_CORS_ORIGINS", None)
        self.assertEqual(load_settings().cors_origins, ("*",))

    def test_environment_defaults_to_development(self):
        os.environ.pop("NOTES_ENV", None)
        self.assertEqual(load_settings().environment, "development")


class NoteTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect("sqlite://:memory:")
        init_db(self.conn)
        self.alice = user_service.register(self.conn, email="alice@example.com", password="a" * 12)
        self.bob = user_service.register(self.conn, email="bob@example.com", password="b" * 12)

    def test_private_note_is_invisible_to_others(self):
        note = note_service.create_note(self.conn, owner_id=self.alice.id, title="draft")
        self.assertTrue(note_service.can_read(self.conn, note=note, user_id=self.alice.id))
        self.assertFalse(note_service.can_read(self.conn, note=note, user_id=self.bob.id))

    def test_share_grants_the_role_it_names(self):
        note = note_service.create_note(self.conn, owner_id=self.alice.id, title="plan")
        note_service.share_note(self.conn, note_id=note.id, owner_id=self.alice.id,
                                user_id=self.bob.id, role="viewer")
        self.assertTrue(note_service.can_read(self.conn, note=note, user_id=self.bob.id))
        self.assertFalse(note_service.can_edit(self.conn, note=note, user_id=self.bob.id))

    def test_only_the_owner_may_delete(self):
        note = note_service.create_note(self.conn, owner_id=self.alice.id, title="keep")
        self.assertFalse(note_service.delete_note(self.conn, note_id=note.id, user_id=self.bob.id))
        self.assertTrue(note_service.delete_note(self.conn, note_id=note.id, user_id=self.alice.id))

    def test_listing_counts_only_what_the_user_may_see(self):
        note_service.create_note(self.conn, owner_id=self.alice.id, title="a")
        note_service.create_note(self.conn, owner_id=self.bob.id, title="b")
        self.assertEqual(note_service.count_notes(self.conn, user_id=self.alice.id), 1)
        note_service.create_note(self.conn, owner_id=self.bob.id, title="c", visibility="public")
        self.assertEqual(note_service.count_notes(self.conn, user_id=self.alice.id), 2)


if __name__ == "__main__":
    unittest.main()
