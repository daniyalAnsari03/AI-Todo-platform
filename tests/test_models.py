# Task T-016 · Spec FR-201–206 §Data Model Changes · Plan §Test-First 3,
# §Data model & persistence · Data-model §1 (SQLModel declaration).

import unittest
from datetime import datetime, timedelta, timezone

from pydantic_core import PydanticUndefined

from sqlmodel import Session, select

from todo_app.models import TodoItem, User
from tests.helpers import configure_test_db, make_test_engine


class TestModels(unittest.TestCase):
    def setUp(self):
        self.engine = make_test_engine()
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(self.engine)  # type: ignore[arg-type]
        self.db = Session(self.engine)  # type: ignore[arg-type]
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        self.db.close()

    def make_user(self, username="alice"):
        return User(
            id=f"user-{username}",
            name=username,
            email=f"{username}@todo.local",
            email_verified=False,
            created_at=self.now,
            updated_at=self.now,
        )

    def test_user_create_read(self):
        user = self.make_user()
        self.db.add(user)
        self.db.commit()
        fetched = self.db.get(User, user.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "alice")
        self.assertEqual(fetched.email, "alice@todo.local")

    def test_user_email_unique(self):
        self.db.add(self.make_user("alice"))
        self.db.commit()
        duplicate = self.make_user("alice")
        self.db.add(duplicate)
        with self.assertRaises(Exception):
            self.db.commit()

    def test_todo_item_create_read_update(self):
        user = self.make_user()
        self.db.add(user)
        self.db.commit()
        item = TodoItem(
            user_id=user.id, title="Buy milk", description="Buy milk", completed=False
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(user)
        self.db.refresh(item)
        self.assertGreater(item.id, 0)
        self.assertEqual(item.description, "Buy milk")
        self.assertFalse(item.completed)

        item.completed = True
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        self.assertTrue(item.completed)

    def test_todo_item_requires_owner(self):
        item = TodoItem(user_id="ghost", description="No owner", completed=False)
        self.db.add(item)
        with self.assertRaises(Exception):
            self.db.commit()

    def test_active_test_db_configured(self):
        import todo_app.database as dbmod

        self.assertTrue(hasattr(dbmod, "configure_engine"))
        self.assertTrue(hasattr(dbmod, "init_db"))


class TestTodoItemTaskFields(unittest.TestCase):
    """FR-201–206: TodoItem gains title/created_at/updated_at; description nullable."""

    def setUp(self):
        self.engine = make_test_engine()
        from sqlmodel import SQLModel

        SQLModel.metadata.create_all(self.engine)  # type: ignore[arg-type]
        self.db = Session(self.engine)  # type: ignore[arg-type]

    def tearDown(self):
        self.db.close()

    def make_user(self, username="alice"):
        now = datetime.now(timezone.utc)
        return User(
            id=f"user-{username}",
            name=username,
            email=f"{username}@todo.local",
            email_verified=False,
            created_at=now,
            updated_at=now,
        )

    def test_title_column_exists_not_nullable(self):
        columns = TodoItem.__table__.columns
        self.assertIn("title", columns)
        self.assertFalse(columns["title"].nullable)

    def test_title_is_required_no_default(self):
        spec = TodoItem.__pydantic_fields__["title"]
        self.assertTrue(spec.is_required())
        self.assertIs(spec.default, PydanticUndefined)

    def test_storing_without_title_fails(self):
        self.db.add(self.make_user())
        self.db.commit()
        item = TodoItem(user_id="user-alice", description="no title")
        self.db.add(item)
        with self.assertRaises(Exception):
            self.db.commit()

    def test_description_column_nullable(self):
        columns = TodoItem.__table__.columns
        self.assertIn("description", columns)
        self.assertTrue(columns["description"].nullable)

    def test_created_at_and_updated_at_set_at_creation(self):
        self.db.add(self.make_user())
        self.db.commit()
        self.db.add(TodoItem(user_id="user-alice", title="Buy milk"))
        self.db.commit()
        item = self.db.exec(select(TodoItem)).first()
        self.assertIsNotNone(item.created_at)
        self.assertIsNotNone(item.updated_at)

    def test_created_at_never_changes(self):
        self.db.add(self.make_user())
        self.db.commit()
        past = (datetime.now(timezone.utc) - timedelta(days=3)).replace(tzinfo=None)
        item = TodoItem(
            user_id="user-alice", title="Keep old date",
            created_at=past, updated_at=past,
        )
        self.db.add(item)
        self.db.commit()
        item.description = "modified"
        self.db.add(item)
        self.db.commit()
        item = self.db.get(TodoItem, item.id)  # type: ignore[arg-type]
        self.assertEqual(item.created_at, past)

    def test_updated_at_changes_only_on_modification(self):
        self.db.add(self.make_user())
        self.db.commit()
        past = (datetime.now(timezone.utc) - timedelta(days=3)).replace(tzinfo=None)
        item = TodoItem(
            user_id="user-alice", title="Timestamp me",
            created_at=past, updated_at=past,
        )
        self.db.add(item)
        self.db.commit()

        # no modification: reading the row must not refresh updated_at
        fetched = self.db.get(TodoItem, item.id)  # type: ignore[arg-type]
        self.assertEqual(fetched.updated_at, past)

        # modification: updated_at must move forward
        fetched.title = "Timestamped"
        self.db.add(fetched)
        self.db.commit()
        refreshed = self.db.get(TodoItem, fetched.id)  # type: ignore[arg-type]
        self.assertNotEqual(refreshed.updated_at, past)
        self.assertGreater(refreshed.updated_at, past)
        self.assertEqual(refreshed.created_at, past)


if __name__ == "__main__":
    unittest.main()