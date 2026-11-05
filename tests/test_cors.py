# Deployment readiness: CORS allowed origins must come from the CORS_ORIGINS
# env var (comma-separated, trimmed, empty entries ignored), defaulting to the
# current localhost values when unset. No wildcard.
import importlib
import os
import unittest

from fastapi.middleware.cors import CORSMiddleware

from todo_app.api import app as app_module


def _cors_allow_origins():
    for middleware in app_module.app.user_middleware:
        if middleware.cls is CORSMiddleware:
            return middleware.kwargs["allow_origins"]
    raise AssertionError("CORSMiddleware not installed")


class TestCorsOrigins(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("CORS_ORIGINS", None)
        importlib.reload(app_module)

    def _reload_with(self, value):
        had = os.environ.pop("CORS_ORIGINS", None)
        try:
            if value is not None:
                os.environ["CORS_ORIGINS"] = value
            importlib.reload(app_module)
            return _cors_allow_origins()
        finally:
            if value is not None:
                os.environ.pop("CORS_ORIGINS", None)
            if had is not None:
                os.environ["CORS_ORIGINS"] = had

    def test_defaults_to_current_localhost_origins_when_unset(self):
        self.assertEqual(
            self._reload_with(None),
            ["http://localhost:3000", "http://127.0.0.1:3000"],
        )

    def test_parses_comma_separated_origins_with_trimming_and_empty_ignored(self):
        self.assertEqual(
            self._reload_with(
                " https://a.example , https://b.example ,,"
            ),
            ["https://a.example", "https://b.example"],
        )

    def test_default_never_contains_wildcard(self):
        origins = self._reload_with(None)
        self.assertNotIn("*", origins)


if __name__ == "__main__":
    unittest.main()
