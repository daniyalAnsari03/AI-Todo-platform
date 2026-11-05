# Task T-005 · Spec §US1 FR-101–108, §Data Model Changes (store parity) · Plan §Phase I console plan (Store API)
"""In-memory todo item store."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

_DESCRIPTION = "description must be non-empty"
_TITLE = "title must be non-empty"
_NO_ITEM = "no item with that id"
_BAD_ID = "id must be a positive integer"


def _utcnow() -> datetime:
    """Return the current UTC time (patch point for tests)."""
    return datetime.now(timezone.utc)


def _normalize_description(description: str | None) -> str | None:
    """Trim the description; empty/whitespace-only becomes None."""
    if description is None:
        return None
    description = description.strip()
    return description or None


@dataclass
class TodoItem:
    """A single todo item stored in memory during a session."""

    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    description: str | None = None
    completed: bool = False


class TodoStore:
    """In-memory store of todo items with sequential positive IDs."""

    def __init__(self) -> None:
        self._items: dict[int, TodoItem] = {}
        self._next_id = 1

    def add(self, title: str, description: str | None = None) -> TodoItem:
        """Create a new item and return it. Rejects empty titles."""
        if not isinstance(title, str) or not title.strip():
            raise ValueError(_TITLE)
        now = _utcnow()
        item = TodoItem(
            id=self._next_id,
            title=title.strip(),
            description=_normalize_description(description),
            created_at=now,
            updated_at=now,
        )
        self._items[item.id] = item
        self._next_id += 1
        return item

    def list_items(self) -> list[TodoItem]:
        """Return current items in insertion order."""
        return list(self._items.values())

    def update(self, item_id: object, title: str, description: str | None) -> None:
        """Rewrite the item's text fields; created_at/id/completed untouched."""
        valid_id = self._validate_id(item_id)
        item = self._get_item(valid_id)
        if not isinstance(title, str) or not title.strip():
            raise ValueError(_TITLE)
        item.title = title.strip()
        item.description = _normalize_description(description)
        item.updated_at = _utcnow()

    def toggle(self, item_id: object) -> None:
        """Flip the item's completed status in either direction."""
        valid_id = self._validate_id(item_id)
        item = self._get_item(valid_id)
        item.completed = not item.completed
        item.updated_at = _utcnow()

    def _validate_id(self, item_id: object) -> int:
        if isinstance(item_id, bool) or not isinstance(item_id, int):
            raise ValueError(_BAD_ID)
        if item_id <= 0:
            raise ValueError(_BAD_ID)
        return item_id

    def _get_item(self, item_id: int) -> TodoItem:
        item = self._items.get(item_id)
        if item is None:
            raise ValueError(_NO_ITEM)
        return item

    def complete(self, item_id: object) -> None:
        """Mark the item with the given id as complete (legacy behavior)."""
        valid_id = self._validate_id(item_id)
        item = self._get_item(valid_id)
        if item.completed:
            raise ValueError("item already complete")
        item.completed = True

    def delete(self, item_id: object) -> None:
        """Remove the item with the given id."""
        valid_id = self._validate_id(item_id)
        if valid_id not in self._items:
            raise ValueError(_NO_ITEM)
        del self._items[valid_id]
