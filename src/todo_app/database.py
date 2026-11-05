# Task T0002 · Spec FR-020–FR-024 §Data Models and Migration Constraints · Plan §OQ-7 (334–345)
from __future__ import annotations

import os

from sqlmodel import Session, SQLModel, create_engine

from . import models  # ensure models are imported

_engine: object | None = None

# Existing Phase II tables that should be created by default
_EXISTING_TABLES = {"user", "session", "account", "verification", "todo_item"}


def _normalize_database_url(url: str) -> str:
    # Task T8120 · Spec 005 amendment: use the installed Phase II PostgreSQL driver.
    if not url:
        return url
    normalized = url.strip()
    if normalized.startswith('postgresql://'):
        return 'postgresql+psycopg2://' + normalized[len('postgresql://'):]
    if normalized.startswith('postgresql+psycopg://'):
        return normalized
    if normalized.startswith('postgres://'):
        return 'postgresql+psycopg2://' + normalized[len('postgres://'):]
    return normalized


def configure_engine(url: str | None = None) -> object:
    """Set the shared engine from *url* (or ``DATABASE_URL``) and return it."""
    global _engine
    if url is None:
        url = os.environ.get("DATABASE_URL", "sqlite://")
    _engine = create_engine(_normalize_database_url(url))
    return _engine


def get_engine() -> object:
    global _engine
    if _engine is None:
        configure_engine()
    return _engine


def init_db(include_chat_tables: bool = False) -> None:
    """Create tables. By default only existing Phase II tables are created; chat tables are migration-only."""
    engine = get_engine()
    if include_chat_tables:
        SQLModel.metadata.create_all(engine)  # type: ignore[arg-type]
        return
    # Create only existing tables
    metadata = SQLModel.metadata
    tables_to_create = [metadata.tables[t] for t in _EXISTING_TABLES if t in metadata.tables]
    if tables_to_create:
        metadata.create_all(engine, tables=tables_to_create)  # type: ignore[arg-type]
    else:
        SQLModel.metadata.create_all(engine)  # type: ignore[arg-type]


def get_db() -> object:
    """FastAPI dependency yielding a SQLModel Session bound to the engine."""
    with Session(get_engine()) as session:  # type: ignore[arg-type]
        yield session