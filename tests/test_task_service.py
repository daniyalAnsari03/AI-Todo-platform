# Task T0103 � Spec FR-002
import unittest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

import todo_app.database as database
from todo_app import models
from todo_app import task_service


class TestTaskService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db()
        with Session(self.engine) as db:
            db.add(models.User(id='u1', name='u', email='u@x.com', email_verified=False))
            db.commit()
        self.db = Session(self.engine)

    def tearDown(self):
        self.db.close()

    def test_crud(self):
        t = task_service.add_task(self.db, 'u1', 'Task 1', 'desc')
        self.assertIsInstance(t, dict)
        tid = t['task_id']
        lst = task_service.list_tasks(self.db, 'u1')
        self.assertTrue(len(lst) >= 1)
        up = task_service.update_task(self.db, 'u1', tid, title='Task 1x')
        self.assertEqual(up['title'], 'Task 1x')
        comp = task_service.complete_task(self.db, 'u1', tid)
        self.assertEqual(comp['status'], 'completed')
        dele = task_service.delete_task(self.db, 'u1', tid)
        self.assertEqual(dele['status'], 'deleted')
