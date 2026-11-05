# Task T0504
import os
import unittest
from unittest import mock
from fastapi.testclient import TestClient

from tests.test_auth import _JwksStubServer, _jwk_entry, _mint_rsa_key, mint_token, ISSUER, AUDIENCE
import todo_app.database as database
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session
from todo_app import models
from todo_app.api.app import create_app


class TestChatKitEndpoint(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db(include_chat_tables=True)
        with Session(self.engine) as db:
            db.add(models.User(id='u1', name='u', email='u@x.com', email_verified=False))
            db.commit()
        self.server = _JwksStubServer()
        self.server.keys = [_jwk_entry(_mint_rsa_key()[1], 'test-kid')]
        env = mock.patch.dict(os.environ, {'JWT_JWKS_URL': self.server.url, 'JWT_ISSUER': ISSUER, 'JWT_AUDIENCE': AUDIENCE})
        env.start()
        self.addCleanup(env.stop)
        app = create_app()
        from todo_app.api import chat, chatkit
        try:
            app.include_router(chat.router)
        except Exception:
            pass
        try:
            app.include_router(chatkit.router)
        except Exception:
            pass
        self.client = TestClient(app)

    def tearDown(self):
        try:
            self.server.close()
        except Exception:
            pass

    def test_missing_token_401(self):
        resp = self.client.post('/api/u1/chatkit', json={})
        self.assertEqual(resp.status_code, 401)
