# Task T8120 · Spec 005 amendment: restore installed Phase II PostgreSQL driver.

import importlib.util
import unittest

from sqlalchemy.engine.url import make_url

from todo_app.database import _normalize_database_url


class TestDatabaseUrlNormalization(unittest.TestCase):
    def test_postgres_urls_resolve_to_importable_installed_driver(self):
        for url in (
            "postgresql://******host/db?sslmode=require",
            "postgres://******host/db?sslmode=require",
        ):
            with self.subTest(scheme=url.split(":", 1)[0]):
                parsed = make_url(_normalize_database_url(url))
                self.assertEqual(parsed.get_backend_name(), "postgresql")
                self.assertEqual(parsed.drivername, "postgresql+psycopg2")
                self.assertIsNotNone(importlib.util.find_spec("psycopg2"))

    def test_sqlite_url_is_unchanged(self):
        url = "sqlite://"

        self.assertEqual(_normalize_database_url(url), url)
        parsed = make_url(_normalize_database_url(url))
        self.assertEqual(parsed.get_backend_name(), "sqlite")
        self.assertIsNotNone(importlib.util.find_spec("sqlite3"))
