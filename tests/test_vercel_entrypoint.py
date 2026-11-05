import tomllib
import unittest
from pathlib import Path

import fastapi

import todo_app.api.app as app_module

ROOT = Path(__file__).resolve().parents[1]


class TestVercelEntrypoint(unittest.TestCase):
    def test_pyproject_vercel_entrypoint(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        tool = data.get("tool", {})
        self.assertEqual(
            tool.get("vercel", {}).get("entrypoint"),
            "src.todo_app.api.app:app",
            "pyproject [tool.vercel] entrypoint must point to src/todo_app/api/app.py",
        )

    def test_pyproject_scripts_app_key_removed(self):
        data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = data["project"]["scripts"]
        self.assertNotIn(
            "app",
            scripts,
            "[project.scripts] must not contain the 'app' key anymore",
        )
        self.assertEqual(
            scripts.get("todo-app"),
            "todo_app:main",
            "todo-app script must remain unchanged",
        )
        self.assertEqual(
            scripts.get("todo-app-api"),
            "todo_app.api.app:main",
            "todo-app-api script must remain unchanged",
        )

    def test_vercelignore_does_not_exclude_frontend_folder(self):
        lines = (ROOT / ".vercelignore").read_text(encoding="utf-8").splitlines()
        banned = {"frontend", "frontend/", "/frontend", "/frontend/"}
        entries = {
            line.strip()
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        }
        offending = entries & banned
        self.assertEqual(
            offending,
            set(),
            "root .vercelignore must not exclude the frontend folder: the frontend "
            "Vercel project builds from Root Directory=frontend, so ignoring 'frontend/' "
            "removes package.json at build time and causes [NEXT_NO_VERSION]",
        )

    def test_app_is_fastapi_instance(self):
        self.assertIsInstance(app_module.app, fastapi.FastAPI)


if __name__ == "__main__":
    unittest.main()
