# Task T0001 · Spec FR-020–FR-024 §Data Models and Migration Constraints · Plan §Data model & migration (265–316)
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import CheckConstraint, Column, Index, Text
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """User account stored in PostgreSQL, managed by Better Auth."""

    __tablename__ = "user"

    id: str = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    email_verified: bool = Field(default=False)
    image: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    sessions: list["Session"] = Relationship(back_populates="user")
    items: list["TodoItem"] = Relationship(back_populates="owner")


class Session(SQLModel, table=True):
    """Better Auth session record for verifying cookies in FastAPI."""

    __tablename__ = "session"

    id: str = Field(primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)

    user: Optional["User"] = Relationship(back_populates="sessions")


class Account(SQLModel, table=True):
    """Better Auth account record (provider link; stores the password hash).

    Column set mirrors Better Auth's drizzle adapter so the same PostgreSQL
    database is shared between the Next.js frontend and the FastAPI backend.
    """

    __tablename__ = "account"

    id: str = Field(primary_key=True)
    account_id: str
    provider_id: str
    user_id: str = Field(foreign_key="user.id")
    access_token: Optional[str] = Field(default=None)
    refresh_token: Optional[str] = Field(default=None)
    id_token: Optional[str] = Field(default=None)
    access_token_expires_at: Optional[datetime] = Field(default=None)
    refresh_token_expires_at: Optional[datetime] = Field(default=None)
    scope: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Verification(SQLModel, table=True):
    """Better Auth verification record."""

    __tablename__ = "verification"

    id: str = Field(primary_key=True)
    identifier: str
    value: str
    expires_at: datetime
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)


class TodoItem(SQLModel, table=True):
    """A single todo item belonging to exactly one user.

    Task T-019 · Spec FR-201–206 §Data Model Changes · Plan §Data model &
    persistence · Data-model §1 (SQLModel declaration). ``title`` required,
    ``description`` nullable, ``created_at`` set at creation and never changed,
    ``updated_at`` refreshed by SQLAlchemy on every UPDATE (onupdate). No
    migration is executed here and the real DB is not touched (isolated-DB
    rule): fresh databases get the target schema via ``init_db()``.
    """

    __tablename__ = "todo_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    title: str
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    owner: Optional["User"] = Relationship(back_populates="items")


class Conversation(SQLModel, table=True):
    """Conversation for Phase III AI chatbot (new table only)."""

    __tablename__ = "conversation"
    __table_args__ = (
        Index("idx_conversation_user_id", "user_id"),
        Index("idx_conversation_chat_thread_id", "chat_thread_id", unique=True),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    chat_thread_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column_kwargs={"onupdate": lambda: datetime.now(timezone.utc)},
    )

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Message(SQLModel, table=True):
    """Message for Phase III AI chatbot (new table only)."""

    __tablename__ = "message"
    __table_args__ = (
        CheckConstraint("role IN ('user','assistant')", name="ck_message_role"),
        Index("idx_message_conversation_id", "conversation_id"),
        Index("idx_message_user_id", "user_id"),
        Index("idx_message_conv_id_id", "conversation_id", "id"),
        Index("idx_message_conv_id_created_at", "conversation_id", "created_at"),
        Index("idx_message_user_conv", "user_id", "conversation_id"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field(sa_column=Column(Text))
    content: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation: Optional["Conversation"] = Relationship(back_populates="messages")