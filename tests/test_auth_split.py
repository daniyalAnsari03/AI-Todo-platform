# Task T0401/T0404 � Spec FR-034, FR-105
import os
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.test_auth import TestJWKBearerAuth, seed_jwt_user, mint_token
from todo_app import auth


class TestAuthSplit(TestJWKBearerAuth):
    def setUp(self):
        super().setUp()
        self.app = FastAPI()

        @self.app.get('/api/{user_id}/test')
        def test_route(user_id: str, user=__import__('fastapi').Depends(auth.get_path_user)):
            return {'ok': True}

    def test_path_mismatch_403_before_db(self):
        seed_jwt_user(self.engine, user_id='user-alice')
        token = mint_token(sub='user-alice')
        resp = self.bearer_app().get('/api/user-bob/test', headers={'Authorization': f'Bearer {token}'}) if False else None
        # use our app
        from fastapi.testclient import TestClient
        client = TestClient(self.app)
        resp = client.get('/api/user-bob/test', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(resp.status_code, 403)
