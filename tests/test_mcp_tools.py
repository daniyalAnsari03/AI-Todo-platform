# Task T0202 — Spec FR-050-FR-057
import unittest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session

import todo_app.database as database
from todo_app import models
from todo_app import mcp_server


class TestMCPTools(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db()
        with Session(self.engine) as db:
            db.add(models.User(id='u1', name='u', email='u@x.com', email_verified=False))
            db.add(models.User(id='u2', name='u2', email='u2@x.com', email_verified=False))
            db.commit()

    def test_add_task_success(self):
        res = mcp_server.add_task('u1', 'Test task', 'desc')
        self.assertIsInstance(res, dict)
        self.assertTrue('task_id' in res or 'id' in res)
        tid = res.get('task_id') or res.get('id')
        self.assertIsNotNone(tid)

    def test_add_task_null_safe_title_and_timestamps(self):
        res = mcp_server.add_task('u1', 't', None)
        self.assertTrue('error' not in res or res.get('error') is None)
        tid = res.get('task_id') or res.get('id')
        # verify persisted with timestamps
        from sqlmodel import select
        with Session(self.engine) as db:
            item = db.get(models.TodoItem, tid)
            self.assertIsNotNone(item.created_at)
            self.assertIsNotNone(item.updated_at)

    def test_list_tasks_all_pending_completed_empty(self):
        # empty
        lst = mcp_server.list_tasks('u1', 'all')
        self.assertIsInstance(lst, dict)
        self.assertEqual(lst.get('tasks'), [])
        # add
        res = mcp_server.add_task('u1', 'a')
        tid = res.get('task_id') or res.get('id')
        lst_all = mcp_server.list_tasks('u1', 'all')
        self.assertIsInstance(lst_all['tasks'], list)
        lst_pending = mcp_server.list_tasks('u1', 'pending')
        self.assertGreaterEqual(len(lst_pending['tasks']), 1)
        mcp_server.complete_task('u1', tid)
        lst_completed = mcp_server.list_tasks('u1', 'completed')
        self.assertGreaterEqual(len(lst_completed['tasks']), 1)

    def test_complete_task_success_not_found_isolation(self):
        res = mcp_server.add_task('u1', 't1')
        tid = res.get('task_id') or res.get('id')
        comp = mcp_server.complete_task('u1', tid)
        self.assertIn(comp.get('status'), ['completed'])
        # not found
        comp_nf = mcp_server.complete_task('u1', 99999)
        self.assertIn('error', comp_nf)
        # cross-user isolation
        res2 = mcp_server.add_task('u1', 't2')
        tid2 = res2.get('task_id') or res2.get('id')
        comp_u2 = mcp_server.complete_task('u2', tid2)
        self.assertIn('error', comp_u2)

    def test_delete_task_success_not_found_isolation(self):
        res = mcp_server.add_task('u1', 't1')
        tid = res.get('task_id') or res.get('id')
        dele = mcp_server.delete_task('u1', tid)
        self.assertIn(dele.get('status'), ['deleted'])
        dele_nf = mcp_server.delete_task('u1', 99999)
        self.assertIn('error', dele_nf)
        res2 = mcp_server.add_task('u1', 't2')
        tid2 = res2.get('task_id') or res2.get('id')
        dele_u2 = mcp_server.delete_task('u2', tid2)
        self.assertIn('error', dele_u2)

    def test_update_task_success_not_found_isolation_null_safe(self):
        res = mcp_server.add_task('u1', 'old')
        tid = res.get('task_id') or res.get('id')
        upd = mcp_server.update_task('u1', tid, title='new', description=None)
        self.assertIsInstance(upd, dict)
        self.assertTrue('error' not in upd or upd.get('error') is None)
        upd_nf = mcp_server.update_task('u1', 99999, title='x')
        self.assertIn('error', upd_nf)
        res2 = mcp_server.add_task('u1', 't2')
        tid2 = res2.get('task_id') or res2.get('id')
        upd_u2 = mcp_server.update_task('u2', tid2, title='x')
        self.assertIn('error', upd_u2)
        upd_bad = mcp_server.update_task('u1', tid)
        self.assertIn('error', upd_bad)

    def test_model_supplied_user_id_ignored_or_rejected(self):
        # model must not be able to act as different user; our API takes user_id as param
        # ensure cross-user still rejected and no privilege escalation
        res = mcp_server.add_task('u1', 't')
        tid = res.get('task_id') or res.get('id')
        # try to pass different user_id explicitly - should be rejected
        comp = mcp_server.complete_task('u2', tid)  # different user
        self.assertIn('error', comp)
        lst = mcp_server.list_tasks('u2', 'all')
        self.assertEqual(lst.get('tasks'), [])

    def test_user_isolation(self):
        res = mcp_server.add_task('u1', 't1')
        tid = res.get('task_id') or res.get('id')
        lst = mcp_server.list_tasks('u2', 'all')
        self.assertEqual(lst.get('tasks'), [])
        comp = mcp_server.complete_task('u2', tid)
        self.assertIn('error', comp)
