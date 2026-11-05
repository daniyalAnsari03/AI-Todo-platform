# Task T0404 — Spec FR-030-FR-035, FR-105
import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

import todo_app.database as database
from todo_app.api.app import create_app
from todo_app.models import User
from tests.test_auth import AUDIENCE, ISSUER, _JwksStubServer, _jwk_entry, _mint_rsa_key, mint_token


class TestChatApi(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db(include_chat_tables=True)
        with Session(self.engine) as db:
            db.add(User(id='user-alice', name='alice', email='alice@todo.local', email_verified=False))
            db.commit()
        self.server = _JwksStubServer()
        self.server.keys = [_jwk_entry(_mint_rsa_key()[1], 'test-kid')]
        env = mock.patch.dict(os.environ, {'JWT_JWKS_URL': self.server.url, 'JWT_ISSUER': ISSUER, 'JWT_AUDIENCE': AUDIENCE})
        env.start()
        self.addCleanup(env.stop)
        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self):
        try:
            self.server.close()
        except Exception:
            pass

    def test_missing_token_401(self):
        resp = self.client.post('/api/user-alice/chat', json={'message': 'hi'})
        self.assertEqual(resp.status_code, 401)

    def test_path_mismatch_403_before_db_access(self):
        resp = self.client.post('/api/user-bob/chat', json={'message': 'hi'}, headers={'Authorization': f'Bearer {mint_token(sub="user-alice")}'})
        self.assertEqual(resp.status_code, 403)

    def test_empty_message_returns_400(self):
        resp = self.client.post('/api/user-alice/chat', json={'message': ''}, headers={'Authorization': f'Bearer {mint_token(sub="user-alice")}'})
        self.assertEqual(resp.status_code, 400)

    def test_valid_request_returns_conversation_id_response_tool_calls(self):
        from todo_app.chat import runner
        class FR:
            def __init__(self):
                self.final_output = 'ok'
                self.new_items = []
        async def fr(agent, input_items, context=None):
            return FR()
        runner.run_agent = fr
        resp = self.client.post('/api/user-alice/chat', json={'message': 'hi'}, headers={'Authorization': f'Bearer {mint_token(sub="user-alice")}'})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('conversation_id', data)
        self.assertIn('response', data)
        self.assertIn('tool_calls', data)
