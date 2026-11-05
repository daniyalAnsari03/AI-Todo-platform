import tomllib
import unittest
from pathlib import Path

import fastapi

import todo_app.api.app as app_module

ROOT = Path(__file__).resolve().parents[1]


class TestVercelEntrypoint(unittest.TestCase):
    def test_pyproject_script_app_points_to_fastapi_app(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = data["project"]["scripts"]
        self.assertIn(
            "app",
            scripts,
            "pyproject [project.scripts] must contain app = 'todo_app.api.app:app' "
            "for the Vercel Python entrypoint",
        )
        self.assertEqual(scripts["app"], "todo_app.api.app:app")

    def test_app_is_fastapi_instance(self):
        self.assertIsInstance(app_module.app, fastapi.FastAPI)


if __name__ == "__main__":
    unittest.main()
