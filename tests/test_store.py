# Task T-002 · Spec §US1 FR-101–108, §Data Model Changes (store parity) · Plan §Phase I console plan, §Test-First 1
import unittest
from datetime import datetime, timezone
from unittest import mock

from todo_app.store import TodoStore


class TestTodoStoreAdd(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_add_assigns_sequential_ids(self):
        item1 = self.store.add("Buy groceries")
        item2 = self.store.add("Clean house")
        self.assertEqual(item1.id, 1)
        self.assertEqual(item2.id, 2)

    def test_add_ids_are_positive(self):
        item = self.store.add("Do laundry")
        self.assertGreater(item.id, 0)

    def test_add_rejects_empty_description(self):
        with self.assertRaises(ValueError):
            self.store.add("")

    def test_add_rejects_whitespace_only_description(self):
        with self.assertRaises(ValueError):
            self.store.add("   ")

    def test_add_rejects_tab_only_description(self):
        with self.assertRaises(ValueError):
            self.store.add("\t\n")

    def test_add_no_item_created_on_rejection(self):
        with self.assertRaises(ValueError):
            self.store.add("")
        self.assertEqual(len(self.store.list_items()), 0)


class TestTodoStoreList(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_list_empty_store(self):
        items = self.store.list_items()
        self.assertEqual(items, [])

    def test_list_returns_items_with_status(self):
        self.store.add("Task one")
        self.store.add("Task two")
        items = self.store.list_items()
        self.assertEqual(len(items), 2)
        self.assertFalse(items[0].completed)
        self.assertFalse(items[1].completed)


class TestTodoStoreComplete(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_complete_flips_status(self):
        item = self.store.add("Write tests")
        self.store.complete(item.id)
        items = self.store.list_items()
        completed_item = next(i for i in items if i.id == item.id)
        self.assertTrue(completed_item.completed)

    def test_complete_already_complete(self):
        item = self.store.add("Already done")
        self.store.complete(item.id)
        with self.assertRaises(ValueError):
            self.store.complete(item.id)

    def test_complete_nonexistent_id(self):
        with self.assertRaises(ValueError):
            self.store.complete(999)


class TestTodoStoreAddWithTitle(unittest.TestCase):
    """FR-103 / FR-105 part 1: title required, description optional."""

    def setUp(self):
        self.store = TodoStore()

    def test_add_persists_title(self):
        item = self.store.add("Buy groceries")
        self.assertEqual(item.title, "Buy groceries")

    def test_add_description_defaults_to_none(self):
        item = self.store.add("Buy groceries")
        self.assertIsNone(item.description)

    def test_add_with_description(self):
        item = self.store.add("Buy groceries", "Milk, eggs, bread")
        self.assertEqual(item.title, "Buy groceries")
        self.assertEqual(item.description, "Milk, eggs, bread")

    def test_add_empty_description_becomes_none(self):
        item = self.store.add("Buy groceries", "")
        self.assertIsNone(item.description)

    def test_add_whitespace_only_description_becomes_none(self):
        item = self.store.add("Buy groceries", "   ")
        self.assertIsNone(item.description)

    def test_add_trims_title_and_description(self):
        item = self.store.add("  Buy groceries  ", "  Milk  ")
        self.assertEqual(item.title, "Buy groceries")
        self.assertEqual(item.description, "Milk")

    def test_add_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            self.store.add("")

    def test_add_rejects_whitespace_only_title(self):
        with self.assertRaises(ValueError):
            self.store.add("   ")

    def test_add_no_item_created_on_title_rejection(self):
        with self.assertRaises(ValueError):
            self.store.add("   ")
        self.assertEqual(len(self.store.list_items()), 0)


class TestTodoStoreTimestamps(unittest.TestCase):
    """created_at/updated_at set on add; refreshed only on update/toggle."""

    def setUp(self):
        self.store = TodoStore()
        self.t0 = datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc)
        self.t1 = datetime(2026, 10, 24, 12, 0, 1, tzinfo=timezone.utc)
        self.t2 = datetime(2026, 10, 24, 12, 0, 2, tzinfo=timezone.utc)

    def test_add_sets_created_at_and_updated_at(self):
        with mock.patch("todo_app.store._utcnow", return_value=self.t0):
            item = self.store.add("Task")
        self.assertEqual(item.created_at, self.t0)
        self.assertEqual(item.updated_at, self.t0)

    def test_update_preserves_created_at_and_refreshes_updated_at(self):
        with mock.patch("todo_app.store._utcnow", return_value=self.t0):
            item = self.store.add("Task")
        with mock.patch("todo_app.store._utcnow", return_value=self.t1):
            self.store.update(item.id, "New title", "New description")
        updated = next(i for i in self.store.list_items() if i.id == item.id)
        self.assertEqual(updated.created_at, self.t0)
        self.assertEqual(updated.updated_at, self.t1)


class TestTodoStoreUpdate(unittest.TestCase):
    """FR-105: rewrite title/description; keep id/completed/created_at."""

    def setUp(self):
        self.store = TodoStore()
        self.item = self.store.add("Buy groceries", "Milk")

    def test_update_rewrites_title_and_description(self):
        self.store.update(self.item.id, "New title", "New description")
        updated = next(i for i in self.store.list_items() if i.id == self.item.id)
        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.description, "New description")

    def test_update_empty_description_becomes_none(self):
        self.store.update(self.item.id, "New title", "")
        updated = next(i for i in self.store.list_items() if i.id == self.item.id)
        self.assertIsNone(updated.description)

    def test_update_preserves_id_and_completed(self):
        self.store.complete(self.item.id)
        self.store.update(self.item.id, "New title", None)
        updated = next(i for i in self.store.list_items() if i.id == self.item.id)
        self.assertEqual(updated.id, self.item.id)
        self.assertTrue(updated.completed)

    def test_update_preserves_created_at(self):
        created_before = self.item.created_at
        self.store.update(self.item.id, "New title", None)
        updated = next(i for i in self.store.list_items() if i.id == self.item.id)
        self.assertEqual(updated.created_at, created_before)

    def test_update_rejects_empty_title(self):
        with self.assertRaises(ValueError):
            self.store.update(self.item.id, "", None)

    def test_update_rejects_whitespace_only_title(self):
        with self.assertRaises(ValueError):
            self.store.update(self.item.id, "   ", None)

    def test_update_unknown_id(self):
        with self.assertRaises(ValueError):
            self.store.update(999, "New title", None)


class TestTodoStoreToggle(unittest.TestCase):
    """FR-107: toggle flips completed in both directions."""

    def setUp(self):
        self.store = TodoStore()
        self.item = self.store.add("Task")

    def test_toggle_incomplete_to_complete(self):
        self.store.toggle(self.item.id)
        updated = next(i for i in self.store.list_items() if i.id == self.item.id)
        self.assertTrue(updated.completed)

    def test_toggle_complete_to_incomplete(self):
        self.store.complete(self.item.id)
        self.store.toggle(self.item.id)
        updated = next(i for i in self.store.list_items() if i.id == self.item.id)
        self.assertFalse(updated.completed)

    def test_toggle_refreshes_updated_at(self):
        t0 = datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 10, 24, 12, 0, 1, tzinfo=timezone.utc)
        with mock.patch("todo_app.store._utcnow", return_value=t0):
            item = self.store.add("Task")
        with mock.patch("todo_app.store._utcnow", return_value=t1):
            self.store.toggle(item.id)
        updated = next(i for i in self.store.list_items() if i.id == item.id)
        self.assertEqual(updated.created_at, t0)
        self.assertEqual(updated.updated_at, t1)

    def test_toggle_unknown_id(self):
        with self.assertRaises(ValueError):
            self.store.toggle(999)


class TestTodoStoreDelete(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_delete_removes_item(self):
        item = self.store.add("Delete me")
        self.store.delete(item.id)
        items = self.store.list_items()
        self.assertEqual(len(items), 0)

    def test_delete_nonexistent_id(self):
        with self.assertRaises(ValueError):
            self.store.delete(999)


class TestTodoStoreIdValidation(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore()

    def test_complete_rejects_non_numeric_id(self):
        with self.assertRaises(ValueError):
            self.store.complete("abc")

    def test_complete_rejects_zero_id(self):
        with self.assertRaises(ValueError):
            self.store.complete(0)

    def test_complete_rejects_negative_id(self):
        with self.assertRaises(ValueError):
            self.store.complete(-1)

    def test_delete_rejects_non_numeric_id(self):
        with self.assertRaises(ValueError):
            self.store.delete("abc")

    def test_delete_rejects_zero_id(self):
        with self.assertRaises(ValueError):
            self.store.delete(0)

    def test_delete_rejects_negative_id(self):
        with self.assertRaises(ValueError):
            self.store.delete(-1)


if __name__ == "__main__":
    unittest.main()
