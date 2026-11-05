# Task T-020a, T-020b, T0102 · Spec FR-210–213, FR-002 · Plan §API plan, §Task service extraction
# Delegates to task_service for behavior parity; auth/validation rules preserved.

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict
from sqlmodel import Session

from .. import task_service
from ..auth import get_current_user, get_path_user, get_token_claims
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/api/{user_id}/tasks", tags=["tasks"])

MAX_TITLE = 200
MAX_DESCRIPTION = 1000


class TaskPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime


class TaskList(BaseModel):
    items: list[TaskPublic]


def authorize_path(path_user_id: str, user: User) -> User:
    """403 when the path user differs from the token user — before any DB lookup."""
    if path_user_id != user.id:
        raise HTTPException(status_code=403, detail="Path user does not match token")
    return user


def parse_task_id(raw_task_id: str) -> int:
    """Non-integer task id path segments are treated as an unknown task (404)."""
    try:
        return int(raw_task_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=404, detail="Task not found") from None


async def read_json_object(request: Request) -> dict:
    """Parse the request body as a JSON object; anything else is a 400."""
    try:
        parsed = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Malformed JSON body") from None
    if not isinstance(parsed, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")
    return parsed


def validate_title(value: object) -> str:
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail="title must be a string")
    title = value.strip()
    if not 1 <= len(title) <= MAX_TITLE:
        raise HTTPException(status_code=400, detail=f"title must be 1-{MAX_TITLE} characters")
    return title


def validate_description(value: object) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise HTTPException(status_code=400, detail="description must be a string")
    if len(value) > MAX_DESCRIPTION:
        raise HTTPException(status_code=400, detail=f"description must be at most {MAX_DESCRIPTION} characters")
    return value


@router.get("", response_model=TaskList)
async def list_tasks(
    user_id: str,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[arg-type]
) -> TaskList:
    current = authorize_path(user_id, user)
    # Use service for parity
    try:
        items = task_service.list_tasks(db, current.id, status="all")
    except task_service.InvalidTaskInput as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    # Reconstruct TaskPublic-like objects via service serialization is dict; convert
    from ..models import TodoItem

    tasks = db.exec(__import__("sqlmodel").select(TodoItem).where(TodoItem.user_id == current.id).order_by(TodoItem.id)).all()
    return TaskList(items=[TaskPublic.model_validate(t) for t in tasks])


@router.post("", response_model=TaskPublic, status_code=201)
async def create_task(
    user_id: str,
    request: Request,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[arg-type]
) -> TaskPublic:
    current = authorize_path(user_id, user)
    body = await read_json_object(request)
    if "title" not in body:
        raise HTTPException(status_code=400, detail="title is required")
    title = validate_title(body["title"])
    description = validate_description(body["description"]) if "description" in body else None
    try:
        result = task_service.add_task(db, current.id, title, description)
    except task_service.InvalidTaskInput as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    # Fetch full object for response_model
    from ..models import TodoItem

    task = db.get(TodoItem, result.get("task_id") or result.get("id"))
    return TaskPublic.model_validate(task)


@router.get("/{task_id}", response_model=TaskPublic)
async def get_task(
    user_id: str,
    task_id: str,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[arg-type]
) -> TaskPublic:
    current = authorize_path(user_id, user)
    tid = parse_task_id(task_id)
    try:
        task = task_service.get_task(db, current.id, tid)
    except task_service.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found") from None
    return TaskPublic.model_validate(task)


@router.put("/{task_id}", response_model=TaskPublic)
async def update_task(
    user_id: str,
    task_id: str,
    request: Request,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[arg-type]
) -> TaskPublic:
    current = authorize_path(user_id, user)
    tid = parse_task_id(task_id)
    # Check ownership first to preserve 404 semantics
    try:
        task = task_service.get_task(db, current.id, tid)
    except task_service.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found") from None
    body = await read_json_object(request)
    if "completed" in body:
        raise HTTPException(status_code=400, detail="completed is not updatable via PUT; use PATCH /complete")
    changes = {}
    if "title" in body:
        changes["title"] = validate_title(body["title"])
    if "description" in body:
        changes["description"] = validate_description(body["description"])
    if not changes:
        # no-op
        return TaskPublic.model_validate(task)
    try:
        task_service.update_task(db, current.id, tid, title=changes.get("title"), description=changes.get("description"))
    except task_service.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found") from None
    except task_service.InvalidTaskInput as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        task = task_service.get_task(db, current.id, tid)
    except task_service.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found") from None
    return TaskPublic.model_validate(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    user_id: str,
    task_id: str,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[arg-type]
) -> Response:
    current = authorize_path(user_id, user)
    tid = parse_task_id(task_id)
    try:
        task_service.delete_task(db, current.id, tid)
    except task_service.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found") from None
    return Response(status_code=204)


@router.patch("/{task_id}/complete", response_model=TaskPublic)
async def toggle_task_complete(
    user_id: str,
    task_id: str,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[arg-type]
) -> TaskPublic:
    current = authorize_path(user_id, user)
    tid = parse_task_id(task_id)
    try:
        # HTTP toggle keeps flipping both directions per original behavior
        task = task_service.get_task(db, current.id, tid)
        from ..models import TodoItem
        from datetime import datetime, timezone

        task.completed = not bool(task.completed)
        task.updated_at = datetime.now(timezone.utc)
        db.add(task)
        db.commit()
        db.refresh(task)
    except task_service.TaskNotFound:
        raise HTTPException(status_code=404, detail="Task not found") from None
    return TaskPublic.model_validate(task)

