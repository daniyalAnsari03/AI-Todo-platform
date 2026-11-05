# Task T0101 · Spec FR-002, FR-050–FR-057 · Plan §Task service extraction (370–381)
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from .models import TodoItem


class TaskNotFound(Exception):
    pass


class InvalidTaskInput(Exception):
    pass


TITLE_MAX = 200
DESC_MAX = 1000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_title(title: str) -> str:
    if title is None:
        raise InvalidTaskInput("title required")
    t = str(title).strip()
    if not t:
        raise InvalidTaskInput("title required")
    if len(t) > TITLE_MAX:
        raise InvalidTaskInput("title too long")
    return t


def _validate_description(description: Optional[str]) -> Optional[str]:
    if description is None:
        return None
    d = str(description)
    if len(d) > DESC_MAX:
        raise InvalidTaskInput("description too long")
    return d


def _serialize_task(item: TodoItem) -> dict:
    created_at = item.created_at.isoformat() if item.created_at is not None else None
    updated_at = item.updated_at.isoformat() if item.updated_at is not None else None
    status = "completed" if bool(item.completed) else "pending"
    return {
        "task_id": item.id,
        "id": item.id,
        "title": item.title or "",
        "description": item.description,
        "status": status,
        "completed": bool(item.completed),
        "created_at": created_at,
        "updated_at": updated_at,
    }


def list_tasks(session: Session, user_id: str, status: str = "all") -> list[dict]:
    status = (status or "all").lower()
    if status not in ("all", "pending", "completed"):
        raise InvalidTaskInput("invalid status")
    stmt = select(TodoItem).where(TodoItem.user_id == user_id)
    items = session.exec(stmt).all()
    result = []
    for item in items:
        s = "completed" if bool(item.completed) else "pending"
        if status != "all" and s != status:
            continue
        result.append(_serialize_task(item))
    return result


def get_task(session: Session, user_id: str, task_id: int) -> TodoItem:
    item = session.get(TodoItem, task_id)
    if not item or item.user_id != user_id:
        raise TaskNotFound("task not found")
    return item


def add_task(session: Session, user_id: str, title: str, description: Optional[str] = None) -> dict:
    t = _validate_title(title)
    d = _validate_description(description)
    now = _now()
    item = TodoItem(user_id=user_id, title=t, description=d, completed=False, created_at=now, updated_at=now)
    session.add(item)
    session.commit()
    session.refresh(item)
    return _serialize_task(item)


def update_task(session: Session, user_id: str, task_id: int, title: Optional[str] = None, description: Optional[str] = None) -> dict:
    if title is None and description is None:
        raise InvalidTaskInput("no fields to update")
    item = get_task(session, user_id, task_id)
    if title is not None:
        item.title = _validate_title(title)
    if description is not None:
        item.description = _validate_description(description)
    item.updated_at = _now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return _serialize_task(item)


def complete_task(session: Session, user_id: str, task_id: int) -> dict:
    item = get_task(session, user_id, task_id)
    item.completed = True
    item.updated_at = _now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"task_id": item.id, "status": "completed", "title": item.title or ""}


def delete_task(session: Session, user_id: str, task_id: int) -> dict:
    item = get_task(session, user_id, task_id)
    title = item.title or ""
    task_id_res = item.id
    session.delete(item)
    session.commit()
    return {"task_id": task_id_res, "status": "deleted", "title": title}
