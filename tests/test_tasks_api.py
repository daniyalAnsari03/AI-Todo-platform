# Task T-017 · Spec FR-210–213 §API Contract §Edge Cases · Plan §Test-First 3 ·
# Contract tasks-api.md (six endpoints) + auth-jwt.md §Backend verification.
# Fresh in-memory SQLite per test; Bearer tokens minted in-test with the test
# RSA key + stubbed JWKS from tests/test_auth.py (no network, no .env reads).
"""Contract tests for the /api/{user_id}/tasks API (US2, FR-210–213)."""

import os
import unittest
import unittest.mock
from datetime import datetime, timedelta, timezone

from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

import todo_app.database as database
from todo_app.api.app import create_app
from todo_app.models import TodoItem, User
from tests.test_auth import (
    AUDIENCE,
    ISSUER,
    _JwksStubServer,
    _jwk_entry,
    _mint_rsa_key,
    mint_token,
)

ALICE = "user-alice"
BOB = "user-bob"
GHOST = "user-nobody"


def utc_naive(days_ago: float = 0) -> datetime:
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=days_ago)).replace(tzinfo=None)


class TestTasksApi(unittest.IsolatedAsyncioTestCase):
    """Six-endpoint matrix: GET/POST/GET id/PUT id/DELETE id/PATCH complete."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        database._engine = self.engine
        database.init_db()
        with Session(self.engine) as db:
            for user_id in (ALICE, BOB):
                db.add(
                    User(
                        id=user_id,
                        name=user_id,
                        email=f"{user_id}@todo.local",
                        email_verified=False,
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc),
                    )
                )
            db.commit()

        self.server = _JwksStubServer()
        self.server.keys = [_jwk_entry(_mint_rsa_key()[1], "test-kid")]
        env = unittest.mock.patch.dict(
            os.environ,
            {
                "JWT_JWKS_URL": self.server.url,
                "JWT_ISSUER": ISSUER,
                "JWT_AUDIENCE": AUDIENCE,
            },
        )
        env.start()
        self.addCleanup(env.stop)

        self.app = create_app()
        self.transport = ASGITransport(app=self.app)
        self.addCleanup(self.server.close)

    def client(self) -> AsyncClient:
        return AsyncClient(transport=self.transport, base_url="http://test")

    def bearer(self, sub: str = ALICE) -> dict:
        return {"Authorization": f"Bearer {mint_token(sub=sub)}"}

    def api(self, sub: str = ALICE, task_id: int | None = None) -> str:
        path = f"/api/{sub}/tasks"
        return path if task_id is None else f"{path}/{task_id}"

    def seed_task(
        self,
        user_id: str = ALICE,
        title: str = "Seed task",
        description: str | None = None,
        completed: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> int:
        with Session(self.engine) as db:
            item = TodoItem(
                user_id=user_id,
                title=title,
                description=description,
                completed=completed,
                created_at=created_at or utc_naive(3),
                updated_at=updated_at or utc_naive(3),
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            return item.id  # type: ignore[return-value]

    # ----------------------------- 401 / 403 gates -----------------------------

    async def test_no_token_401_on_all_six_endpoints(self):
        targets = (
            ("GET", self.api(), None),
            ("POST", self.api(), {"title": "x"}),
            ("GET", self.api(task_id=1), None),
            ("PUT", self.api(task_id=1), {"title": "x"}),
            ("DELETE", self.api(task_id=1), None),
            ("PATCH", self.api(task_id=1) + "/complete", None),
        )
        async with self.client() as c:
            for method, path, body in targets:
                resp = await c.request(method, path, json=body)
                self.assertEqual(resp.status_code, 401, f"{method} {path}")
                self.assertIn("detail", resp.json())

    async def test_foreign_user_id_403_before_any_db_lookup(self):
        """Existing foreign user → 403 on all six endpoints, {"detail": "..."}."""
        targets = (
            ("GET", self.api(BOB), None),
            ("POST", self.api(BOB), {"title": "x"}),
            ("GET", self.api(BOB, 1), None),
            ("PUT", self.api(BOB, 1), {"title": "x"}),
            ("DELETE", self.api(BOB, 1), None),
            ("PATCH", self.api(BOB, 1) + "/complete", None),
        )
        async with self.client() as c:
            for method, path, body in targets:
                resp = await c.request(method, path, headers=self.bearer(), json=body)
                self.assertEqual(resp.status_code, 403, f"{method} {path}")
                self.assertIn("detail", resp.json())

    async def test_nonexistent_foreign_user_id_still_403_never_404(self):
        """403 is decided from the token+path match alone — no DB lookup, no 404."""
        async with self.client() as c:
            targets = (
                ("GET", self.api(GHOST), None),
                ("POST", self.api(GHOST), {"title": "x"}),
                ("GET", self.api(GHOST, 1), None),
                ("PUT", self.api(GHOST, 1), {"title": "x"}),
                ("DELETE", self.api(GHOST, 1), None),
                ("PATCH", self.api(GHOST, 1) + "/complete", None),
            )
            for method, path, body in targets:
                resp = await c.request(method, path, headers=self.bearer(), json=body)
                self.assertEqual(resp.status_code, 403, f"{method} {path}")
                self.assertIn("detail", resp.json())

    # ------------------------------- list/create/get -------------------------------

    async def test_list_envelope_empty(self):
        async with self.client() as c:
            resp = await c.get(self.api(), headers=self.bearer())
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), {"items": []})

    async def test_list_envelope_returns_token_users_tasks_ordered_by_id(self):
        first = self.seed_task(title="One")
        second = self.seed_task(title="Two", description="desc")
        # bob's task must not leak into alice's list
        self.seed_task(user_id=BOB, title="Bobs")
        async with self.client() as c:
            resp = await c.get(self.api(), headers=self.bearer())
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(set(body.keys()), {"items"})
            self.assertEqual([t["id"] for t in body["items"]], [first, second])
            self.assertEqual(
                [t["user_id"] for t in body["items"]], [ALICE, ALICE]
            )

    async def test_task_json_shape(self):
        created = utc_naive(2)
        task_id = self.seed_task(
            title="Shape", description="Shape desc", created_at=created,
            updated_at=created,
        )
        async with self.client() as c:
            resp = await c.get(self.api(task_id=task_id), headers=self.bearer())
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(
                set(body.keys()),
                {"id", "user_id", "title", "description", "completed",
                 "created_at", "updated_at"},
            )
            self.assertEqual(body["user_id"], ALICE)
            self.assertEqual(body["title"], "Shape")
            self.assertEqual(body["description"], "Shape desc")
            self.assertFalse(body["completed"])
            self.assertIn(str(created.date()), body["created_at"])

    async def test_create_task_201_with_defaults(self):
        async with self.client() as c:
            resp = await c.post(
                self.api(), headers=self.bearer(),
                json={"title": "Buy milk", "description": "2% or oat"},
            )
            self.assertEqual(resp.status_code, 201)
            body = resp.json()
            self.assertGreater(body["id"], 0)
            self.assertEqual(body["user_id"], ALICE)
            self.assertEqual(body["title"], "Buy milk")
            self.assertEqual(body["description"], "2% or oat")
            self.assertFalse(body["completed"])
            self.assertIsNotNone(body["created_at"])
            self.assertIsNotNone(body["updated_at"])

    async def test_create_without_description_stores_null(self):
        async with self.client() as c:
            resp = await c.post(
                self.api(), headers=self.bearer(), json={"title": "No description"}
            )
            self.assertEqual(resp.status_code, 201)
            self.assertIsNone(resp.json()["description"])

            listed = await c.get(self.api(), headers=self.bearer())
            self.assertIsNone(listed.json()["items"][0]["description"])

    async def test_get_task_200(self):
        task_id = self.seed_task(title="Get me", description="desc")
        async with self.client() as c:
            resp = await c.get(self.api(task_id=task_id), headers=self.bearer())
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json()["title"], "Get me")

    # ------------------------------- 404 (no leak) -------------------------------

    async def test_unknown_task_id_404_on_get_put_delete_patch(self):
        async with self.client() as c:
            # positive control: a real task must be served (router exists)
            own = self.seed_task(title="Real")
            found = await c.get(self.api(task_id=own), headers=self.bearer())
            self.assertEqual(found.status_code, 200)
            for method, body in (
                ("GET", None),
                ("PUT", {"title": "x"}),
                ("DELETE", None),
                ("PATCH", None),
            ):
                url = self.api(task_id=999)
                if method == "PATCH":
                    url += "/complete"
                resp = await c.request(method, url, headers=self.bearer(), json=body)
                self.assertEqual(resp.status_code, 404, f"{method} {url}")
                self.assertIn("detail", resp.json())

    async def test_foreign_owned_task_id_404_no_enumeration_leak(self):
        alice_task = self.seed_task(user_id=ALICE, title="Alices")
        bob_task = self.seed_task(user_id=BOB, title="Bobs")
        async with self.client() as c:
            # Alice asks about bob's task within her own namespace → indistinguishable 404.
            resp = await c.get(self.api(task_id=bob_task), headers=self.bearer())
            self.assertEqual(resp.status_code, 404)
            missing = await c.get(self.api(task_id=99999), headers=self.bearer())
            self.assertEqual(missing.status_code, 404)
            # no ownership/existence distinction exposed (tasks-api.md)
            self.assertEqual(resp.json()["detail"], missing.json()["detail"])
            # sanity: her own task is found
            own = await c.get(self.api(task_id=alice_task), headers=self.bearer())
            self.assertEqual(own.status_code, 200)

    async def test_non_integer_task_id_404(self):
        async with self.client() as c:
            # positive control: the integer id route must exist and serve tasks
            own = self.seed_task(title="Real")
            found = await c.get(self.api(task_id=own), headers=self.bearer())
            self.assertEqual(found.status_code, 200)
            for method, suffix in (
                ("GET", ""),
                ("PUT", ""),
                ("DELETE", ""),
                ("PATCH", "/complete"),
            ):
                url = self.api(task_id="not-a-number") + suffix
                resp = await c.request(method, url, headers=self.bearer())
                self.assertEqual(resp.status_code, 404, f"{method} {url}")
                self.assertIn("detail", resp.json())

    # ------------------------------- validation -------------------------------

    async def test_title_200_ok_201_rejected(self):
        async with self.client() as c:
            ok = await c.post(
                self.api(), headers=self.bearer(), json={"title": "a" * 200}
            )
            self.assertEqual(ok.status_code, 201)
            too_long = await c.post(
                self.api(), headers=self.bearer(), json={"title": "a" * 201}
            )
            self.assertIn(too_long.status_code, (400, 422))
            self.assertIn("detail", too_long.json())
            listed = await c.get(self.api(), headers=self.bearer())
            self.assertEqual(len(listed.json()["items"]), 1)

    async def test_description_1000_ok_1001_rejected(self):
        async with self.client() as c:
            ok = await c.post(
                self.api(),
                headers=self.bearer(),
                json={"title": "ok", "description": "d" * 1000},
            )
            self.assertEqual(ok.status_code, 201)
            too_long = await c.post(
                self.api(),
                headers=self.bearer(),
                json={"title": "bad", "description": "d" * 1001},
            )
            self.assertIn(too_long.status_code, (400, 422))
            self.assertIn("detail", too_long.json())
            listed = await c.get(self.api(), headers=self.bearer())
            self.assertEqual(len(listed.json()["items"]), 1)

    async def test_whitespace_title_rejected_400(self):
        async with self.client() as c:
            for bad in ("", "   ", "\t\n"):
                resp = await c.post(
                    self.api(), headers=self.bearer(), json={"title": bad}
                )
                self.assertEqual(resp.status_code, 400, repr(bad))
                self.assertIn("detail", resp.json())
            listed = await c.get(self.api(), headers=self.bearer())
            self.assertEqual(listed.json(), {"items": []})

    async def test_missing_title_rejected(self):
        async with self.client() as c:
            resp = await c.post(self.api(), headers=self.bearer(), json={})
            self.assertIn(resp.status_code, (400, 422))

    async def test_wrong_types_rejected_no_state_change(self):
        task_id = self.seed_task(title="Untouched")
        async with self.client() as c:
            cases = (
                ("POST", self.api(), {"title": 123}),
                ("POST", self.api(), {"title": None}),
                ("POST", self.api(), {"title": "ok", "description": 5}),
                ("PUT", self.api(task_id=task_id), {"title": 123}),
                ("PUT", self.api(task_id=task_id), {"description": ["x"]}),
            )
            for method, url, body in cases:
                resp = await c.request(method, url, headers=self.bearer(), json=body)
                self.assertIn(resp.status_code, (400, 422), f"{method} {body}")
                self.assertIn("detail", resp.json())
            fetched = await c.get(self.api(task_id=task_id), headers=self.bearer())
            self.assertEqual(fetched.json()["title"], "Untouched")

    async def test_malformed_json_rejected_no_state_change(self):
        task_id = self.seed_task(title="Intact")
        async with self.client() as c:
            for method, url in (
                ("POST", self.api()),
                ("PUT", self.api(task_id=task_id)),
            ):
                resp = await c.request(
                    method, url, headers=self.bearer(), content=b"{not json"
                )
                self.assertIn(resp.status_code, (400, 422), method)
                self.assertIn("detail", resp.json())
            fetched = await c.get(self.api(task_id=task_id), headers=self.bearer())
            self.assertEqual(fetched.json()["title"], "Intact")

    # ------------------------------- PUT semantics -------------------------------

    async def test_put_updates_fields_and_refreshes_updated_at(self):
        task_id = self.seed_task(title="Old title", description="Old desc")
        past = utc_naive(3)
        with Session(self.engine) as db:
            item = db.get(TodoItem, task_id)  # type: ignore[arg-type]
            item.updated_at = past
            db.commit()
        async with self.client() as c:
            resp = await c.put(
                self.api(task_id=task_id), headers=self.bearer(),
                json={"title": "New title", "description": "New desc"},
            )
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["title"], "New title")
            self.assertEqual(body["description"], "New desc")
            self.assertNotEqual(body["updated_at"], str(past))
            self.assertIn(str(past.date()), body["created_at"])

    async def test_put_empty_object_200_noop_without_bumping_updated_at(self):
        task_id = self.seed_task(title="Same", description="same")
        past = utc_naive(3)
        with Session(self.engine) as db:
            item = db.get(TodoItem, task_id)  # type: ignore[arg-type]
            item.updated_at = past
            db.commit()
        async with self.client() as c:
            before = await c.get(self.api(task_id=task_id), headers=self.bearer())
            resp = await c.put(
                self.api(task_id=task_id), headers=self.bearer(), json={}
            )
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.json(), before.json())

    async def test_put_partial_update_preserves_absent_fields(self):
        task_id = self.seed_task(title="Only title moves", description="keep me")
        past = utc_naive(3)
        with Session(self.engine) as db:
            item = db.get(TodoItem, task_id)  # type: ignore[arg-type]
            item.updated_at = past
            db.commit()
        async with self.client() as c:
            resp = await c.put(
                self.api(task_id=task_id), headers=self.bearer(),
                json={"title": "Moved"},
            )
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["title"], "Moved")
            self.assertEqual(body["description"], "keep me")
            self.assertNotEqual(body["updated_at"], str(past))

    async def test_put_completed_is_not_updatable(self):
        task_id = self.seed_task(title="Toggle-free zone", completed=False)
        async with self.client() as c:
            resp = await c.put(
                self.api(task_id=task_id), headers=self.bearer(),
                json={"completed": True, "title": "Cheeky update"},
            )
            self.assertIn(resp.status_code, (400, 422))
            self.assertIn("detail", resp.json())
            fetched = await c.get(self.api(task_id=task_id), headers=self.bearer())
            self.assertFalse(fetched.json()["completed"])
            self.assertEqual(fetched.json()["title"], "Toggle-free zone")

    async def test_put_whitespace_title_rejected(self):
        task_id = self.seed_task(title="Original")
        async with self.client() as c:
            resp = await c.put(
                self.api(task_id=task_id), headers=self.bearer(), json={"title": "  "}
            )
            self.assertEqual(resp.status_code, 400)
            fetched = await c.get(self.api(task_id=task_id), headers=self.bearer())
            self.assertEqual(fetched.json()["title"], "Original")

    # ------------------------------- DELETE -------------------------------

    async def test_delete_204_and_task_permanently_gone(self):
        task_id = self.seed_task(title="Delete me")
        async with self.client() as c:
            resp = await c.delete(self.api(task_id=task_id), headers=self.bearer())
            self.assertEqual(resp.status_code, 204)
            self.assertEqual(resp.content, b"")
            for method, url in (
                ("GET", self.api(task_id=task_id)),
                ("PUT", self.api(task_id=task_id)),
                ("DELETE", self.api(task_id=task_id)),
                ("PATCH", self.api(task_id=task_id) + "/complete"),
            ):
                gone = await c.request(method, url, headers=self.bearer())
                self.assertEqual(gone.status_code, 404, f"{method} {url}")

    # ------------------------------- PATCH complete -------------------------------

    async def test_patch_complete_toggles_both_directions_and_refreshes_updated_at(self):
        task_id = self.seed_task(title="Toggle me", completed=False)
        past = utc_naive(3)
        with Session(self.engine) as db:
            item = db.get(TodoItem, task_id)  # type: ignore[arg-type]
            item.updated_at = past
            db.commit()
        async with self.client() as c:
            first = await c.patch(
                self.api(task_id=task_id) + "/complete", headers=self.bearer()
            )
            self.assertEqual(first.status_code, 200)
            self.assertTrue(first.json()["completed"])
            self.assertNotEqual(first.json()["updated_at"], str(past))
            self.assertIn(str(past.date()), first.json()["created_at"])

            back = await c.patch(
                self.api(task_id=task_id) + "/complete", headers=self.bearer()
            )
            self.assertEqual(back.status_code, 200)
            self.assertFalse(back.json()["completed"])
            self.assertNotEqual(back.json()["updated_at"], str(past))

    # ------------------------------- isolation -------------------------------

    async def test_two_user_isolation(self):
        alice_task = self.seed_task(user_id=ALICE, title="Alice task")
        bob_task = self.seed_task(user_id=BOB, title="Bob task")
        async with self.client() as c:
            alice_list = await c.get(self.api(), headers=self.bearer())
            self.assertEqual(
                [t["id"] for t in alice_list.json()["items"]], [alice_task]
            )
            bob_list = await c.get(self.api(BOB), headers=self.bearer(BOB))
            self.assertEqual(
                [t["id"] for t in bob_list.json()["items"]], [bob_task]
            )
            apocalypse = await c.get(
                self.api(task_id=bob_task), headers=self.bearer()
            )
            self.assertEqual(apocalypse.status_code, 404)

    async def test_bearer_for_other_user_on_own_path_uses_token_user(self):
        """Data served belongs to the token user, not the path (path must match)."""
        alice_task = self.seed_task(user_id=ALICE, title="Alice task")
        async with self.client() as c:
            resp = await c.get(self.api(BOB, alice_task), headers=self.bearer())
            self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
