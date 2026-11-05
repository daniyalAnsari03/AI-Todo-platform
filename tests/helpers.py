"""Shared test helpers. Not a unittest module (does not start with ``test_``)."""

from __future__ import annotations

import base64
import urllib.parse
from datetime import datetime, timedelta, timezone

from sqlmodel import Session
from sqlalchemy import create_engine, event
from sqlalchemy.pool import StaticPool

from todo_app.models import Session as AuthSession, TodoItem, User


def signed_cookie_value(token: str, signature: bytes = bytes(range(32))) -> str:
    """Build the wire value of a Better Auth signed session cookie.

    Better Auth writes ``encodeURIComponent(token + "." + base64_hmac)`` and the
    browser echoes that verbatim in the ``Cookie`` request header, so the
    regression tests must exercise the percent-encoded form. The database
    stores only the raw ``token``.
    """
    digest = base64.b64encode(signature).decode()
    return urllib.parse.quote(f"{token}.{digest}", safe="")


def make_test_engine(url: str = "sqlite://", *, enforce_fk: bool = True):
    """Create a shared in-memory SQLite engine with StaticPool.

    Set *enforce_fk* to ``True`` (default) to enable ``PRAGMA foreign_keys=ON``,
    which is required for realistic FK behaviour and the orphan-session tests
    in ``test_models.py``.
    """
    engine = create_engine(
        url, connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    if enforce_fk:

        @event.listens_for(engine, "connect")
        def _enable_sqlite_fk(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def configure_test_db():
    """Point the app modules at an isolated in-memory SQLite DB."""
    engine = make_test_engine()
    import todo_app.database as dbmod

    dbmod._engine = engine
    dbmod.init_db()
    return engine


def seed_user_and_session(
    db: Session,
    username: str = "alice",
    token: str = "valid-session-token",
    expire_hours: int = 1,
) -> tuple[User, str]:
    """Create a User + Session row directly (mimics Better Auth writes)."""
    now = datetime.now(timezone.utc)
    user = User(
        id=f"user-{username}",
        name=username,
        email=f"{username}@todo.local",
        email_verified=False,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.flush()  # ensure user PK is persisted before session FK references it

    session = AuthSession(
        id=f"session-{token}",
        token=token,
        user_id=user.id,
        expires_at=now + timedelta(hours=expire_hours),
        created_at=now,
        updated_at=now,
    )
    db.add(session)
    db.commit()
    db.refresh(user)
    return user, token


def add_item(db: Session, user: User, description: str, completed: bool = False) -> TodoItem:
    item = TodoItem(user_id=user.id, description=description, completed=completed)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item