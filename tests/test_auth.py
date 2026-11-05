# Task T-010, T-011, T-013-support; T-014 retirement edit · Spec §US3
# (FR-220–229), FR-228 · Plan §Test-First 2, §Auth plan, §OQ-3 · Contract
# auth-jwt.md (Option A: JWKS/RS256). Legacy cookie tests were REMOVED together
# with the cookie code at T-014 (same-release retirement); the backend now
# authenticates via Bearer JWT only.

import json
import os
import threading
import unittest
import unittest.mock
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session

from todo_app.auth import get_current_user
from todo_app.models import User
from tests.helpers import configure_test_db


ENV_KEYS = ("BETTER_AUTH_URL", "JWT_JWKS_URL", "JWT_ISSUER", "JWT_AUDIENCE")

ISSUER = "http://test-better-auth.local"
AUDIENCE = ISSUER


@contextmanager
def without_jwt_env():
    """Temporarily remove all JWT verification config keys from the environ."""
    saved = {key: os.environ.pop(key) for key in ENV_KEYS if key in os.environ}
    try:
        yield
    finally:
        os.environ.update(saved)


def seed_jwt_user(engine, user_id: str = "user-alice", username: str = "alice") -> None:
    """Persist a user row for JWT ``sub`` lookups (idempotent)."""
    with Session(engine) as db:
        if db.get(User, user_id) is None:
            now = datetime.now(timezone.utc)
            db.add(
                User(
                    id=user_id,
                    name=username,
                    email=f"{username}@todo.local",
                    email_verified=False,
                    created_at=now,
                    updated_at=now,
                )
            )
            db.commit()


class _JwksHandler(BaseHTTPRequestHandler):
    """Serves the JWKS document held by the test ``_JwksStubServer`` instance."""

    def do_GET(self):
        server = self.server  # the ThreadingHTTPServer; state set by the wrapper
        server.request_count += 1
        if server.open:
            body = json.dumps({"keys": list(server.keys)}).encode()
            self.send_response(200)
        else:
            body = b'{"detail": "gone"}'
            self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class _JwksStubServer:
    """A JWKS endpoint on a random localhost port (no external network).

    Counts every HTTP request so the caching / refresh-on-unknown-``kid``
    contract (auth-jwt.md §Option A) can be asserted exactly.
    """

    def __init__(self):
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _JwksHandler)
        self._httpd.keys: list[dict] = []
        self._httpd.request_count = 0
        self._httpd.open = True
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True
        )
        self._thread.start()

    @property
    def keys(self) -> list[dict]:
        return self._httpd.keys

    @keys.setter
    def keys(self, value: list[dict]) -> None:
        self._httpd.keys = value

    @property
    def request_count(self) -> int:
        return self._httpd.request_count

    @property
    def open(self) -> bool:
        return self._httpd.open

    @open.setter
    def open(self, value: bool) -> None:
        self._httpd.open = value

    @property
    def port(self):
        return self._httpd.server_address[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}"

    def close(self):
        if not self.open:
            return
        self.open = False
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)


@cache
def _mint_rsa_key():
    """A test RSA keypair: (private_key, public_key)."""
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key, key.public_key()


@cache
def _wrong_rsa_key():
    """A second RSA key sole for wrong-signature minting."""
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwk_entry(public_key, kid: str) -> dict:
    import jwt

    entry = jwt.algorithms.RSAAlgorithm.to_jwk(public_key, as_dict=True)
    entry.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return entry


def mint_token(
    *,
    sub: str = "user-alice",
    kid: str = "test-kid",
    key=None,
    alg: str = "RS256",
    iss: str = ISSUER,
    aud: str = AUDIENCE,
    exp=None,
    headers=None,
) -> str:
    """Mint an RS256 JWT exactly like Better Auth's jwt plugin would."""
    import jwt

    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iss": iss,
        "aud": aud,
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": exp if exp is not None else int((now + timedelta(hours=1)).timestamp()),
    }
    merged_headers = {"kid": kid}
    if headers:
        merged_headers.update(headers)
    if key is None:
        key = _mint_rsa_key()[0]
    if alg == "none":
        key = None
    return jwt.encode(payload, key, algorithm=alg, headers=merged_headers)


class TestJWKBearerAuth(unittest.TestCase):
    """FR-220–229: Authorization: Bearer is verified against the plugin's JWKS."""

    @classmethod
    def setUpClass(cls):
        cls.engine = configure_test_db()
        cls.server = _JwksStubServer()
        (_, cls.public_key) = _mint_rsa_key()
        cls.server.keys = [_jwk_entry(cls.public_key, "test-kid")]

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def setUp(self):
        patcher = unittest.mock.patch.dict(
            os.environ,
            {
                "JWT_JWKS_URL": self.server.url,
                "JWT_ISSUER": ISSUER,
                "JWT_AUDIENCE": AUDIENCE,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def bearer_app(self):
        """Probe app covering the six future task paths + /whoami."""
        app = FastAPI()
        token_user_dep = get_current_user

        @app.get("/whoami")
        def whoami(user: User = Depends(token_user_dep)):  # type: ignore[assignment]
            return {"id": user.id}

        @app.get("/api/{user_id}/tasks")
        @app.post("/api/{user_id}/tasks")
        @app.get("/api/{user_id}/tasks/{item_id}")
        @app.put("/api/{user_id}/tasks/{item_id}")
        @app.delete("/api/{user_id}/tasks/{item_id}")
        @app.patch("/api/{user_id}/tasks/{item_id}")
        def any_task_path(  # type: ignore[empty-body]
            user_id: str,
            item_id: str = "",
            user: User = Depends(token_user_dep),
        ):
            return {"user": user.id, "path_user": user_id}

        return TestClient(app)

    def request_bearer(self, headers=None, path="/whoami"):
        client = self.bearer_app()
        return client.get(path, headers=headers or {})

    def test_missing_header_401_on_all_six_task_paths(self):
        client = self.bearer_app()
        targets = (
            ("GET", "/api/u1/tasks"),
            ("POST", "/api/u1/tasks"),
            ("GET", "/api/u1/tasks/1"),
            ("PUT", "/api/u1/tasks/1"),
            ("DELETE", "/api/u1/tasks/1"),
            ("PATCH", "/api/u1/tasks/1"),
        )
        for method, path in targets:
            resp = client.request(method, path)
            self.assertEqual(resp.status_code, 401, f"{method} {path}")

    def test_malformed_authorization_header_401(self):
        client = self.bearer_app()
        token = mint_token()
        cases = (
            None,  # header absent
            "Bearer",
            "Bearer   ",
            "Basic dXNlcjpwYXNz",
            f"Bearer {token} extra-part",
        )
        for authorization in cases:
            with self.subTest(authorization=authorization or "<absent>"):
                headers = {} if authorization is None else {"Authorization": authorization}
                resp = client.get("/whoami", headers=headers)
                self.assertEqual(resp.status_code, 401)

    def test_case_insensitive_bearer_scheme_accepted(self):
        self.seed_user("alice")
        resp = self.request_bearer(
            {"Authorization": f"bearer {mint_token(sub='user-alice')}"}
        )
        self.assertEqual(resp.status_code, 200)

    def test_wrong_signature_401(self):
        self.seed_user("alice")
        forged = mint_token(sub="user-alice", key=_wrong_rsa_key())
        resp = self.request_bearer({"Authorization": f"Bearer {forged}"})
        self.assertEqual(resp.status_code, 401)

    def test_expired_token_60s_leeway_boundary(self):
        """Leeway is exactly 60 s: expired-59s-ago passes, expired-65s-ago fails."""
        self.seed_user("alice")
        now = datetime.now(timezone.utc)
        fresh_resp = self.request_bearer(
            {
                "Authorization": "Bearer "
                + mint_token(sub="user-alice", exp=int((now - timedelta(seconds=55)).timestamp()))
            }
        )
        self.assertEqual(fresh_resp.status_code, 200)
        stale_resp = self.request_bearer(
            {
                "Authorization": "Bearer "
                + mint_token(sub="user-alice", exp=int((now - timedelta(seconds=65)).timestamp()))
            }
        )
        self.assertEqual(stale_resp.status_code, 401)
        self.assertEqual(stale_resp.json()["detail"], "Token expired")

    def test_unknown_kid_401(self):
        self.seed_user("alice")
        unknown = mint_token(sub="user-alice", kid="rotated-away-kid")
        resp = self.request_bearer({"Authorization": f"Bearer {unknown}"})
        self.assertEqual(resp.status_code, 401)

    def test_wrong_issuer_401(self):
        self.seed_user("alice")
        token = mint_token(sub="user-alice", iss="http://not-the-issuer.local")
        resp = self.request_bearer({"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401)

    def test_wrong_audience_401(self):
        self.seed_user("alice")
        token = mint_token(sub="user-alice", aud="http://not-the-audience.local")
        resp = self.request_bearer({"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401)

    def test_alg_none_rejected(self):
        """alg: none must never verify (NFR-003 allowlist; fail closed)."""
        self.seed_user("alice")
        token = mint_token(sub="user-alice", alg="none")
        resp = self.request_bearer({"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401)

    def test_sha_signed_token_rejected_no_downgrade(self):
        """HS256 forgery with a kid matching the JWKS: no silent downgrade."""
        self.seed_user("alice")
        hmac_key = b"forty-two-bytes-of-attacker-secret-000"
        token = mint_token(
            sub="user-alice",
            alg="HS256",
            key=hmac_key,
        )
        resp = self.request_bearer({"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401)

    def test_valid_token_extracts_user(self):
        self.seed_user("alice")
        resp = self.request_bearer(
            {"Authorization": f"Bearer {mint_token(sub='user-alice')}"}
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["id"], "user-alice")

    def test_token_user_missing_in_db_401(self):
        """A valid token for a user absent from the DB must 401."""
        self.seed_user("alice")
        resp = self.request_bearer(
            {"Authorization": f"Bearer {mint_token(sub='user-ghost')}"}
        )
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()["detail"], "User not found")

    def seed_user(self, username: str, user_id: str | None = None):
        now = datetime.now(timezone.utc)
        user = User(
            id=user_id or f"user-{username}",
            name=username,
            email=f"{username}@todo.local",
            email_verified=False,
            created_at=now,
            updated_at=now,
        )
        with Session(self.engine) as db:
            if db.get(User, user.id) is None:
                db.add(user)
                db.commit()
        return user


class TestJWKSCachingAndFailures(unittest.TestCase):
    """FR-222 (Amendment 1): JWKS caching, one refresh-on-unknown-kid, 503s."""

    @classmethod
    def setUpClass(cls):
        cls.engine = configure_test_db()
        (_, cls.public_key) = _mint_rsa_key()

    def fresh_server(self):
        server = _JwksStubServer()
        server.keys = [_jwk_entry(self.public_key, "known-kid")]
        self.addCleanup(server.close)
        return server

    def jwt_env(self, jwks_url: str):
        patcher = unittest.mock.patch.dict(
            os.environ,
            {"JWT_JWKS_URL": jwks_url, "JWT_ISSUER": ISSUER, "JWT_AUDIENCE": AUDIENCE},
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def unauthenticated_whoami(self, token: str):
        client = TestClient(self.app)
        return client.get("/whoami", headers={"Authorization": f"Bearer {token}"})

    def setUp(self):
        seed_jwt_user(self.engine)
        self.app = FastAPI()

        @self.app.get("/whoami")
        def whoami(user: User = Depends(get_current_user)):  # type: ignore[assignment]
            return {"id": user.id}

    def test_keys_cached_second_verification_makes_no_http_call(self):
        server = self.fresh_server()
        self.jwt_env(server.url)
        token = mint_token(sub="user-alice", kid="known-kid")
        first = self.unauthenticated_whoami(token)
        self.assertEqual(first.status_code, 200)
        calls_after_first = server.request_count
        self.assertEqual(calls_after_first, 1)
        second = self.unauthenticated_whoami(token)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(server.request_count, calls_after_first)

    def test_unknown_kid_triggers_exactly_one_refresh_then_401(self):
        server = self.fresh_server()
        self.jwt_env(server.url)
        token = mint_token(sub="user-alice", kid="never-published-kid")
        resp = self.unauthenticated_whoami(token)
        self.assertEqual(resp.status_code, 401)
        # 1 initial fetch + exactly ONE refresh for the unknown kid — nothing more.
        self.assertEqual(server.request_count, 2)

    def test_unreachable_jwks_first_use_503(self):
        closed_server = self.fresh_server()
        closed_port = closed_server.port
        closed_server.close()
        self.jwt_env(f"http://127.0.0.1:{closed_port}")
        token = mint_token(sub="user-alice", kid="known-kid")
        resp = self.unauthenticated_whoami(token)
        self.assertEqual(resp.status_code, 503)
        self.assertIn("detail", resp.json())

    def test_unreachable_jwks_on_unknown_kid_refresh_503(self):
        """Stale cache exists, refresh fails: 503, never stale-key acceptance."""
        server = self.fresh_server()
        self.jwt_env(server.url)
        warm = self.unauthenticated_whoami(mint_token(sub="user-alice", kid="known-kid"))
        self.assertEqual(warm.status_code, 200)  # cache primed (1 fetch)
        cached_calls = server.request_count
        server.close()  # endpoint now unreachable
        rotated = mint_token(sub="user-alice", kid="rotated-kid")
        resp = self.unauthenticated_whoami(rotated)
        self.assertEqual(resp.status_code, 503)
        self.assertGreaterEqual(cached_calls, 1)


class TestJWTStartupFailFast(unittest.TestCase):
    """NFR-002: missing JWT/JWKS config → the app refuses to start with a clear error."""

    def assert_app_refuses_to_start(self):
        import todo_app.api.app as app_module

        app = app_module.create_app()
        with self.assertRaises(RuntimeError) as ctx:
            with TestClient(app):
                pass
        return ctx.exception

    def test_startup_fails_when_all_jwt_config_missing(self):
        with without_jwt_env():
            error = self.assert_app_refuses_to_start()
        self.assertIn("JWT", str(error))

    def test_startup_fails_when_issuer_and_audience_missing(self):
        with unittest.mock.patch.dict(os.environ, {}, clear=False), without_jwt_env():
            os.environ["JWT_JWKS_URL"] = "http://127.0.0.1:9/jwks"
            error = self.assert_app_refuses_to_start()
        self.assertIn("JWT", str(error))


if __name__ == "__main__":
    unittest.main()