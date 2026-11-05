# Task T0504
import unittest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

import todo_app.database as database
from todo_app import models
from todo_app.chat.store import SqlModelChatKitStore


class TestChatKitStore(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db(include_chat_tables=True)
        with Session(self.engine) as db:
            db.add(models.User(id='u1', name='u', email='u@x.com', email_verified=False))
            db.commit()
        self.store = SqlModelChatKitStore(self.engine)

    def test_generate_thread_id(self):
        tid = self.store.generate_thread_id(type('C',(),{'user_id':'u1'})())
        self.assertTrue(tid.startswith('thread_'))

    def test_thread_create_load_add_message_mapping(self):
        import asyncio
        ctx = type('Ctx', (), {'user_id': 'u1'})()
        # create/save thread
        from chatkit.types import ThreadMetadata
        thread = ThreadMetadata(id='thread_123', created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc))
        asyncio.get_event_loop().run_until_complete(self.store.save_thread(thread, ctx))
        # load
        loaded = asyncio.get_event_loop().run_until_complete(self.store.load_thread('thread_123', ctx))
        self.assertIsNotNone(loaded)
        # add message
        from chatkit.types import UserMessageItem, UserMessageTextContent
        item = UserMessageItem(id='item_1', thread_id='thread_123', content=[UserMessageTextContent(text='hi')], created_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc), attachments=[], inference_options={})
        asyncio.get_event_loop().run_until_complete(self.store.add_thread_item('thread_123', item, ctx))
        # load items
        from chatkit.store import Page
        page = asyncio.get_event_loop().run_until_complete(self.store.load_thread_items('thread_123', None, 10, 'asc', ctx))
        self.assertIsInstance(page, Page)
        self.assertTrue(len(page.data) >= 1)
