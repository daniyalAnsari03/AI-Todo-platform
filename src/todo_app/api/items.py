# RETIRED (Task T-014 + T-021) — DO NOT IMPORT: this /api/items router is
# unmounted and unreferenced (spec OQ-2 hard-replace, FR-211, FR-228 ·
# Contract tasks-api.md §Retired routes). Kept on disk only pending
# user-authorized deletion per the implementation-run no-delete override.

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from ..auth import get_current_user
from ..database import get_db
from ..models import TodoItem, User

router = APIRouter(prefix="/api/items", tags=["items"])


class ItemCreate(BaseModel):
    description: str


class ItemUpdate(BaseModel):
    completed: Any


class ItemPublic(BaseModel):
    id: int
    description: str
    completed: bool


class ItemList(BaseModel):
    items: list[ItemPublic]


def to_public(item: TodoItem) -> ItemPublic:
    return ItemPublic(id=item.id, description=item.description, completed=item.completed)


@router.get("", response_model=ItemList)
def list_items(
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[assignment]
) -> ItemList:
    items = db.exec(
        select(TodoItem).where(TodoItem.user_id == user.id).order_by(TodoItem.id)
    ).all()
    return ItemList(items=[to_public(i) for i in items])


@router.post("", response_model=ItemPublic, status_code=201)
def add_item(
    payload: ItemCreate,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[assignment]
) -> ItemPublic:
    if not payload.description.strip():
        raise HTTPException(status_code=400, detail="Description cannot be empty")
    item = TodoItem(
        user_id=user.id, description=payload.description.strip(), completed=False
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_public(item)


@router.patch("/{item_id}", response_model=ItemPublic)
def update_item(
    item_id: int,
    payload: ItemUpdate,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[assignment]
) -> ItemPublic:
    if not isinstance(payload.completed, bool) or not payload.completed:
        raise HTTPException(status_code=400, detail="Only marking complete is supported")
    item = get_owned_item(db, user, item_id)
    item.completed = True
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_public(item)


@router.delete("/{item_id}", status_code=204)
def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),  # type: ignore[assignment]
    db: Session = Depends(get_db),  # type: ignore[assignment]
) -> Response:
    item = get_owned_item(db, user, item_id)
    db.delete(item)
    db.commit()
    return Response(status_code=204)


def get_owned_item(db: Session, user: User, item_id: int) -> TodoItem:
    item = db.get(TodoItem, item_id)
    if item is None or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Item not found")
    return item