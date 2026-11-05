# Task T0404 — Spec FR-030-FR-042
import unittest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

import todo_app.database as database
from todo_app import models
from todo_app.chat.service import ChatService


class FakeAgent:
    pass


class FakeResult:
    def __init__(self):
        self.final_output = 'Hello'
        self.new_items = []
        self.output = None


class TestChatService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db(include_chat_tables=True)
        with Session(self.engine) as db:
            db.add(models.User(id='user-1', name='u', email='u@x.com', email_verified=False))
            db.commit()

    def test_new_conversation_when_conversation_id_absent(self):
        db = Session(self.engine)
        svc = ChatService(agent=FakeAgent())
        from todo_app.chat import runner
        async def fr(agent, input_items, context=None):
            return FakeResult()
        runner.run_agent = fr
        import asyncio
        res = asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'hi'))
        self.assertIn('conversation_id', res)
        self.assertIn('response', res)
        self.assertIn('tool_calls', res)
        # verify persisted
        with Session(self.engine) as db2:
            conv = db2.get(models.Conversation, res['conversation_id'])
            self.assertIsNotNone(conv)
            msgs = db2.exec(__import__('sqlmodel').select(models.Message).where(models.Message.conversation_id == conv.id)).all()
            self.assertEqual(len(msgs), 2)  # user + assistant

    def test_conversation_resume_with_history(self):
        db = Session(self.engine)
        svc = ChatService(agent=FakeAgent())
        from todo_app.chat import runner
        async def fr(agent, input_items, context=None):
            r = FakeResult()
            r.final_output = 'Hi there'
            return r
        runner.run_agent = fr
        import asyncio
        res1 = asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'hello'))
        cid = res1['conversation_id']
        # second message in same conversation - history should be loaded
        async def fr2(agent, input_items, context=None):
            self.assertTrue(any(i.get('role') == 'user' and i.get('content') == 'hello' for i in input_items))
            r = FakeResult()
            r.final_output = 'followup'
            return r
        runner.run_agent = fr2
        res2 = asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'again', conversation_id=cid))
        self.assertEqual(res2['conversation_id'], cid)
        with Session(self.engine) as db2:
            msgs = db2.exec(__import__('sqlmodel').select(models.Message).where(models.Message.conversation_id == cid).order_by(models.Message.created_at, models.Message.id)).all()
            self.assertEqual(len(msgs), 4)

    def test_another_users_conversation_id_rejected(self):
        db = Session(self.engine)
        svc = ChatService(agent=FakeAgent())
        from todo_app.chat import runner
        async def fr(agent, input_items, context=None):
            return FakeResult()
        runner.run_agent = fr
        import asyncio
        res1 = asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'hi'))
        cid = res1['conversation_id']
        with Session(self.engine) as db2:
            db2.add(models.User(id='user-2', name='u2', email='u2@x.com', email_verified=False))
            db2.commit()
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            asyncio.get_event_loop().run_until_complete(svc.handle_chat(db2, 'user-2', 'hi', conversation_id=cid))
        self.assertEqual(cm.exception.status_code, 404)

    def test_user_and_assistant_messages_persisted(self):
        db = Session(self.engine)
        svc = ChatService(agent=FakeAgent())
        from todo_app.chat import runner
        async def fr(agent, input_items, context=None):
            return FakeResult()
        runner.run_agent = fr
        import asyncio
        res = asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'msg'))
        with Session(self.engine) as db2:
            msgs = db2.exec(__import__('sqlmodel').select(models.Message).where(models.Message.conversation_id == res['conversation_id'])).all()
            roles = {m.role for m in msgs}
            self.assertIn('user', roles)
            self.assertIn('assistant', roles)

    def test_upstream_openai_failure_returns_friendly_error_no_stack_trace(self):
        db = Session(self.engine)
        svc = ChatService(agent=FakeAgent())
        from todo_app.chat import runner
        async def fr_bad(agent, input_items, context=None):
            raise Exception('boom')
        runner.run_agent = fr_bad
        import asyncio
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'hi'))
        self.assertEqual(cm.exception.status_code, 502)
        self.assertIn('Assistant unavailable', str(cm.exception.detail))
        # no stack trace in detail
        self.assertNotIn('Traceback', str(cm.exception.detail))

    def test_restart_resume_build_fresh_service_instance_same_db(self):
        db = Session(self.engine)
        svc = ChatService(agent=FakeAgent())
        from todo_app.chat import runner
        async def fr(agent, input_items, context=None):
            r = FakeResult()
            r.final_output = 'first'
            return r
        runner.run_agent = fr
        import asyncio
        res = asyncio.get_event_loop().run_until_complete(svc.handle_chat(db, 'user-1', 'hello'))
        cid = res['conversation_id']
        # fresh instance
        db2 = Session(self.engine)
        svc2 = ChatService(agent=FakeAgent())
        async def fr2(agent, input_items, context=None):
            self.assertTrue(len(input_items) >= 1)  # history should load
            r = FakeResult()
            r.final_output = 'second'
            return r
        runner.run_agent = fr2
        res2 = asyncio.get_event_loop().run_until_complete(svc2.handle_chat(db2, 'user-1', 'again', conversation_id=cid))
        self.assertEqual(res2['conversation_id'], cid)
        with Session(self.engine) as db3:
            msgs = db3.exec(__import__('sqlmodel').select(models.Message).where(models.Message.conversation_id == cid)).all()
            self.assertEqual(len(msgs), 4)
