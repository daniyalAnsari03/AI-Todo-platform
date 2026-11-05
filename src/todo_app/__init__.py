# Task T-006 · Spec §US1 FR-104–108 · Plan §Phase I console plan (CLI surface), §OQ-5
"""Console Todo CLI: text-in / text-out REPL with in-memory storage."""

from __future__ import annotations

import sys
from typing import TextIO

from .store import TodoStore

HELP = """\
Commands:
  add <title> | <description>          Add a new item (description optional)
  add <text>                           Add an item (whole text becomes the title)
  list                                 List all todo items
  update <id> <title> | <description>  Update an item's title and description
  toggle <id>                          Toggle an item between complete and incomplete
  complete <id>                        Mark an item as complete
  delete <id>                          Delete an item
  exit                                 Exit the application
  help                                 Show this help message
"""


def _parse_id(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError:
        raise ValueError("id must be a positive integer") from None
    if value <= 0:
        raise ValueError("id must be a positive integer")
    return value


def _split_title_description(text: str) -> tuple[str, str | None]:
    """Split `title | description`; without `|` the whole text is the title."""
    if "|" not in text:
        return text.strip(), None
    raw_title, _, raw_description = text.partition("|")
    return raw_title.strip(), raw_description


def _find_item(store: TodoStore, item_id: int):
    return next((item for item in store.list_items() if item.id == item_id), None)


def main(stdin: TextIO | None = None, stdout: TextIO | None = None, stderr: TextIO | None = None) -> int:
    """Run the interactive REPL, returning the process exit code."""
    store = TodoStore()
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr

    for line in stdin:
        parts = line.strip().split(maxsplit=1)
        if not parts:
            continue
        command = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if command == "add":
            try:
                title, description = _split_title_description(arg)
                item = store.add(title, description)
            except ValueError as exc:
                print(f"Error: {exc}", file=stderr)
                continue
            print(f"Added item {item.id}: {item.title}", file=stdout)
        elif command == "list":
            items = store.list_items()
            if not items:
                print("No items stored.", file=stdout)
                continue
            for item in items:
                status = "complete" if item.completed else "incomplete"
                if item.description:
                    print(
                        f"{item.id}. {item.title} — {item.description} [{status}]",
                        file=stdout,
                    )
                else:
                    print(f"{item.id}. {item.title} [{status}]", file=stdout)
        elif command == "update":
            id_raw, _, text = arg.partition(" ")
            try:
                item_id = _parse_id(id_raw)
            except ValueError as exc:
                print(f"Error: {exc}", file=stderr)
                continue
            title, description = _split_title_description(text)
            try:
                store.update(item_id, title, description)
            except ValueError as exc:
                print(f"Error: {exc}", file=stderr)
                continue
            item = _find_item(store, item_id)
            print(f"Updated item {item.id}: {item.title}", file=stdout)
        elif command == "toggle":
            try:
                item_id = _parse_id(arg)
                store.toggle(item_id)
            except ValueError as exc:
                print(f"Error: {exc}", file=stderr)
                continue
            item = _find_item(store, item_id)
            status = "complete" if item.completed else "incomplete"
            print(f"Toggled item {item.id}: {item.title} [{status}]", file=stdout)
        elif command == "complete":
            try:
                item_id = _parse_id(arg)
                store.complete(item_id)
            except ValueError as exc:
                print(f"Error: {exc}", file=stderr)
                continue
            item = _find_item(store, item_id)
            print(f"Completed item {item.id}: {item.title}", file=stdout)
        elif command == "delete":
            try:
                item_id = _parse_id(arg)
            except ValueError as exc:
                print(f"Error: {exc}", file=stderr)
                continue
            item = _find_item(store, item_id)
            if item is None:
                print("Error: no item with that id", file=stderr)
                continue
            store.delete(item_id)
            print(f"Deleted item {item.id}: {item.title}", file=stdout)
        elif command == "exit":
            return 0
        else:
            print(HELP, file=stdout)

    return 0
