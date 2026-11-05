# Task T0004/T0704 extended — Spec FR-020-FR-024, FR-090, FR-208
from __future__ import annotations

import unittest
from datetime import datetime

from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import StaticPool

from todo_app import migrations
from todo_app import database
from sqlmodel import SQLModel
from todo_app import models


class TestChatMigration(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db()

    def test_create_chat_tables(self):
        res = migrations.create_chat_tables(self.engine)
        with self.engine.connect() as conn:
            tables = inspect(conn).get_table_names()
        self.assertIn('conversation', tables)
        self.assertIn('message', tables)
        res2 = migrations.create_chat_tables(self.engine)
        self.assertFalse(res2['changed'])


class TestMigrate003(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db()
        # create legacy shape? init_db creates target shape via SQLModel.metadata.create_all
        # but migrate_003 expects legacy todo_item without title/created_at/updated_at
        # need to recreate legacy
        from sqlmodel import Session
        SQLModel.metadata.drop_all(self.engine)
        # create user and legacy todo_item
        with self.engine.begin() as conn:
            conn.exec_driver_sql("CREATE TABLE user (id TEXT PRIMARY KEY, name TEXT, email TEXT, email_verified BOOL, image TEXT, created_at TIMESTAMP, updated_at TIMESTAMP)")
            conn.exec_driver_sql("CREATE TABLE todo_item (id INTEGER PRIMARY KEY, user_id TEXT NOT NULL REFERENCES user(id), description TEXT NOT NULL, completed BOOL NOT NULL DEFAULT 0)")
            conn.exec_driver_sql("INSERT INTO user (id,name,email,email_verified) VALUES ('u1','u','u@x.com',0)")
            conn.exec_driver_sql("INSERT INTO todo_item (user_id, description, completed) VALUES ('u1','hello world',0)")

    def test_migrate_003_backfills(self):
        res = migrations.migrate_003(self.engine)
        self.assertTrue(res['changed'])
        with self.engine.connect() as conn:
            cols = [c['name'] for c in inspect(conn).get_columns('todo_item')]
            self.assertIn('title', cols)
            self.assertIn('created_at', cols)
            self.assertIn('updated_at', cols)
            rows = conn.exec_driver_sql("SELECT title, description, created_at, updated_at FROM todo_item").fetchall()
            self.assertEqual(rows[0][0], 'hello world')
            self.assertEqual(rows[0][1], 'hello world')
            self.assertEqual(rows[0][2], rows[0][3])

    def test_migrate_003_idempotent(self):
        migrations.migrate_003(self.engine)
        res = migrations.migrate_003(self.engine)
        self.assertFalse(res['changed'])
        self.assertTrue(res.get('skipped'))

    def test_plan_migrate_003(self):
        plan = migrations.plan_migrate_003(self.engine)
        self.assertTrue(any('title' in p for p in plan))
        migrations.migrate_003(self.engine)
        plan2 = migrations.plan_migrate_003(self.engine)
        self.assertTrue(any('already' in p.lower() for p in plan2))


class TestJwksMigration(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine
        database.init_db()

    def test_create_jwks_table(self):
        res = migrations.create_jwks_table(self.engine)
        self.assertTrue(res['changed'])
        with self.engine.connect() as conn:
            tables = inspect(conn).get_table_names()
        self.assertIn('jwks', tables)
        res2 = migrations.create_jwks_table(self.engine)
        self.assertFalse(res2['changed'])

    def test_plan_create_jwks(self):
        plan = migrations.plan_create_jwks(self.engine)
        self.assertTrue(any('jwks' in p for p in plan))
        migrations.create_jwks_table(self.engine)
        plan2 = migrations.plan_create_jwks(self.engine)
        self.assertTrue(any('already' in p.lower() for p in plan2))


class TestMigrationSmoke(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        database._engine = self.engine

    def test_all_migrations_idempotent(self):
        SQLModel.metadata.create_all(self.engine)
        r1 = migrations.create_chat_tables(self.engine)
        r2 = migrations.create_jwks_table(self.engine)
        r3 = migrations.create_chat_tables(self.engine)
        r4 = migrations.create_jwks_table(self.engine)
        self.assertFalse(r3['changed'])
        self.assertFalse(r4['changed'])
