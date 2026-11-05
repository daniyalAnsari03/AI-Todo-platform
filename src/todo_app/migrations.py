# Task T-025 · Spec FR-208, SC-007 §US5 · Plan §Implementation ordering step 3,
# §OQ-1 (Option 2 lossless), §OQ-7 (single-timestamp backfill) · Data-model
# §2–5 (steps, post-conditions, jwks table DDL, rollback). Idempotent migration;
# runs an ephemeral-DB-friendly, dialect-aware transaction (SQLite tests /
# PostgreSQL real run, approval-gated). Reads DATABASE_URL from the environment
# at runtime only and NEVER prints or logs it (NFR-001).

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone

from sqlalchemy import create_engine, inspect, text

TITLE_MAX = 200

NEW_COLUMNS = ("title", "created_at", "updated_at")

JWKS_COLUMNS = (
    "id",
    "public_key",
    "private_key",
    "created_at",
    "expires_at",
    "alg",
    "crv",
)

# Better Auth jwks table (Data-model §4, exact column names/types).
JWKS_DDL = """
CREATE TABLE jwks (
    id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    private_key TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP,
    alg TEXT,
    crv TEXT
)
"""

# SQLite target-shape DDL used for the not-null drop (SQLite cannot ALTER
# NOT NULL in place; the table is rebuilt inside the same transaction).
SQLITE_TARGET_DDL = """
CREATE TABLE todo_item (
    id INTEGER PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES user(id),
    title TEXT NOT NULL,
    description TEXT,
    completed BOOL NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
"""

def _table_columns(conn, table: str) -> list[str]:
    return [c["name"] for c in inspect(conn).get_columns(table)]


def _table_row_count(conn, table: str) -> int:
    return int(conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one())


def _redact(message: str, url: str) -> str:
    """Strip any accidental connection-string occurrence (NFR-001)."""
    return message.replace(url, "<redacted>") if url else message


def migrate_003(engine) -> dict:
    """Idempotent US5 migration of ``todo_item`` (Data-model §2–3).

    Lossless legacy mapping: ``title`` = first 200 characters of
    ``description``; ``description`` keeps the full original byte-for-byte;
    ``created_at`` = ``updated_at`` = one now() timestamp for the whole run;
    ``description`` becomes nullable. Post-condition assertions run inside the
    single transaction; any violation fails fast and rolls everything back.
    """
    with engine.connect() as conn:
        if "todo_item" not in inspect(conn).get_table_names():
            raise RuntimeError("todo_item table not found on this database")
        already = _table_columns(conn, "todo_item")

    if "title" in already:
        return {"changed": False, "skipped": True, "reason": "already migrated", "rows": None}

    timestamps_type = {"postgresql": "TIMESTAMPTZ"}.get(
        engine.dialect.name, "TIMESTAMP"
    )
    is_pg = engine.dialect.name == "postgresql"
    now = datetime.now(timezone.utc)
    backfill_ts: object
    if is_pg:
        backfill_ts = now  # real datetime scalar for Postgres (TIMESTAMPTZ)
    else:
        backfill_ts = now.strftime("%Y-%m-%d %H:%M:%S.%f")  # SQLite stores TEXT

    with engine.begin() as conn:
        columns = _table_columns(conn, "todo_item")
        if "title" in columns:  # defensive re-check inside the transaction
            return {"changed": False, "skipped": True, "reason": "already migrated", "rows": None}

        rows_before = _table_row_count(conn, "todo_item")
        originals = dict(
            conn.execute(text("SELECT id, description FROM todo_item")).all()
        )

        # -- Data-model §3 steps: add columns, backfill, relax description ----
        conn.execute(text("ALTER TABLE todo_item ADD COLUMN title TEXT"))
        conn.execute(text(f"ALTER TABLE todo_item ADD COLUMN created_at {timestamps_type}"))
        conn.execute(text(f"ALTER TABLE todo_item ADD COLUMN updated_at {timestamps_type}"))

        if is_pg:
            conn.execute(
                text(
                    "UPDATE todo_item SET title = LEFT(description, :n), "
                    "created_at = :ts, updated_at = :ts"
                ),
                {"n": TITLE_MAX, "ts": backfill_ts},
            )
        else:
            conn.execute(
                text(
                    "UPDATE todo_item SET title = SUBSTR(description, 1, :n), "
                    "created_at = :ts, updated_at = :ts"
                ),
                {"n": TITLE_MAX, "ts": backfill_ts},
            )

        if is_pg:
            conn.execute(
                text("ALTER TABLE todo_item ALTER COLUMN description DROP NOT NULL")
            )
        else:
            # SQLite: rebuild the table with description nullable (safe copy).
            conn.execute(text("ALTER TABLE todo_item RENAME TO todo_item_m003_old"))
            conn.execute(text(SQLITE_TARGET_DDL))
            conn.execute(
                text(
                    "INSERT INTO todo_item (id, user_id, title, description, "
                    "completed, created_at, updated_at) "
                    "SELECT id, user_id, title, description, completed, "
                    "created_at, updated_at FROM todo_item_m003_old"
                )
            )
            conn.execute(text("DROP TABLE todo_item_m003_old"))

        # -- Data-model §3 post-conditions (fail fast → rollback) -------------
        rows_after = _table_row_count(conn, "todo_item")
        if rows_after != rows_before:
            raise RuntimeError(f"row count changed: {rows_before} -> {rows_after}")

        migrated = conn.execute(
            text(
                "SELECT id, title, description, created_at, updated_at FROM todo_item"
            )
        ).all()
        for row_id, title, description, created_at, updated_at in migrated:
            if title is None:
                raise RuntimeError(f"post-condition violated: row {row_id} has NULL title")
            if len(title) > TITLE_MAX:
                raise RuntimeError(
                    f"post-condition violated: row {row_id} title exceeds {TITLE_MAX} chars"
                )
            if description != originals.get(row_id):
                raise RuntimeError(
                    f"post-condition violated: row {row_id} description text changed"
                )
            if (description or "")[:TITLE_MAX] != title or not description.startswith(title):
                raise RuntimeError(
                    f"post-condition violated: row {row_id} not lossless-prefixed"
                )
            if created_at != updated_at or created_at is None or updated_at is None:
                raise RuntimeError(
                    f"post-condition violated: row {row_id} timestamp backfill invalid"
                )

    return {"changed": True, "skipped": False, "reason": None, "rows": rows_before}


def plan_migrate_003(engine) -> list[str]:
    """Read-only dry-run: what WOULD change (never writes anything)."""
    with engine.connect() as conn:
        tables = inspect(conn).get_table_names()
        if "todo_item" not in tables:
            return ["todo_item table not present on this database: nothing to migrate"]
        columns = _table_columns(conn, "todo_item")
        rows = _table_row_count(conn, "todo_item")

    if "title" in columns:
        return [
            "todo_item is already migrated: no changes WOULD be made "
            f"({rows} rows present)"
        ]

    missing = [c for c in NEW_COLUMNS if c not in columns]
    description_not_null = "description" in columns
    return [
        f"WOULD add columns: {missing}",
        f"WOULD backfill {rows} rows (title = first "
        f"{TITLE_MAX} chars of description; created_at = updated_at = one run timestamp)",
        f"WOULD make description nullable{'' if description_not_null else ' (column absent)'}",
    ]


def create_jwks_table(engine) -> dict:
    """Create the Better Auth ``jwks`` table (Data-model §4) when absent."""
    with engine.begin() as conn:
        if "jwks" in inspect(conn).get_table_names():
            return {"changed": False, "skipped": True}
        conn.execute(text(JWKS_DDL))
        columns = _table_columns(conn, "jwks")
        if columns != list(JWKS_COLUMNS):
            raise RuntimeError(f"post-condition violated: unexpected jwks columns {columns}")
    return {"changed": True, "skipped": False}


def plan_create_jwks(engine) -> list[str]:
    """Read-only dry-run for the jwks table."""
    with engine.connect() as conn:
        exists = "jwks" in inspect(conn).get_table_names()
    return (
        ["jwks table already exists: no changes WOULD be made"]
        if exists
        else [f"WOULD create table jwks with columns: {', '.join(JWKS_COLUMNS)}"]
    )


# Task T0003 · Spec FR-020–FR-024, FR-090 · Plan §318–345
def create_chat_tables(engine) -> dict:
    """Create conversation and message tables idempotently (new tables only)."""
    from sqlmodel import SQLModel
    from . import models  # ensure models imported

    with engine.begin() as conn:
        tables = inspect(conn).get_table_names()
        changed = False
        if "conversation" not in tables:
            SQLModel.metadata.tables["conversation"].create(bind=conn, checkfirst=True)
            changed = True
        else:
            pass
        tables = inspect(conn).get_table_names()
        if "message" not in tables:
            SQLModel.metadata.tables["message"].create(bind=conn, checkfirst=True)
            changed = True
    # Post-conditions
    with engine.connect() as conn:
        tables = inspect(conn).get_table_names()
        if "conversation" not in tables or "message" not in tables:
            raise RuntimeError("post-condition violated: chat tables not created")
        conv_cols = _table_columns(conn, "conversation")
        msg_cols = _table_columns(conn, "message")
        expected_conv = {"id", "user_id", "chat_thread_id", "created_at", "updated_at"}
        expected_msg = {"id", "user_id", "conversation_id", "role", "content", "created_at"}
        if not expected_conv.issubset(set(conv_cols)) or not expected_msg.issubset(set(msg_cols)):
            raise RuntimeError("post-condition violated: unexpected chat columns")
        if "todo_item" not in tables:
            pass  # should exist in normal cases
    if not changed:
        return {"changed": False, "skipped": True}
    return {"changed": True, "skipped": False}


def plan_create_chat_tables(engine) -> list[str]:
    """Read-only dry-run for chat tables."""
    with engine.connect() as conn:
        tables = inspect(conn).get_table_names()
    plans = []
    if "conversation" not in tables:
        plans.append("WOULD create table conversation (id, user_id, chat_thread_id, created_at, updated_at) with indexes")
    else:
        plans.append("conversation table already exists: no changes WOULD be made")
    if "message" not in tables:
        plans.append("WOULD create table message (id, user_id, conversation_id, role, content, created_at) with CHECK(role IN ('user','assistant')) and indexes; ON DELETE CASCADE via FK")
    else:
        plans.append("message table already exists: no changes WOULD be made")
    return plans if plans else ["chat tables already exist: no changes WOULD be made"]


def _engine_from_env():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("Error: DATABASE_URL is not set in the environment.", file=sys.stderr)
        return None
    try:
        return create_engine(url)
    except Exception as exc:  # noqa: BLE001 — report, never leak the URL
        print(f"Error: cannot create engine: {_redact(str(exc), url)}", file=sys.stderr)
        return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m todo_app.migrations",
        description=(
            "US5 schema migration runner (Data-model §3–4). Reads DATABASE_URL "
            "from the environment at runtime; never prints or logs it."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="read-only: report what WOULD change without writing anything",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "migrate-todo-item",
        help="run the idempotent todo_item migration (title/created_at/updated_at)",
    )
    subparsers.add_parser(
        "create-jwks", help="create the Better Auth jwks table when absent"
    )
    subparsers.add_parser(
        "create-chat-tables", help="create conversation and message tables when absent"
    )
    args = parser.parse_args(argv)

    url = os.environ.get("DATABASE_URL")  # kept only for message redaction
    engine = _engine_from_env()
    if engine is None:
        return 1
    try:
        if args.command == "migrate-todo-item":
            if args.dry_run:
                for line in plan_migrate_003(engine):
                    print(line)
            else:
                result = migrate_003(engine)
                if result["changed"]:
                    print(f"todo_item migration applied: {result['rows']} rows backfilled.")
                else:
                    print("todo_item migration skipped (already applied); no changes made.")
        elif args.command == "create-jwks":
            if args.dry_run:
                for line in plan_create_jwks(engine):
                    print(line)
            else:
                result = create_jwks_table(engine)
                print(
                    "jwks table created."
                    if result["changed"]
                    else "jwks table already exists; no changes made."
                )
        elif args.command == "create-chat-tables":
            if args.dry_run:
                for line in plan_create_chat_tables(engine):
                    print(line)
            else:
                result = create_chat_tables(engine)
                print(
                    "chat tables created."
                    if result["changed"]
                    else "chat tables already exist; no changes made."
                )
        else:
            parser.print_help()
            return 1
    except Exception as exc:  # noqa: BLE001 — fail fast; transaction rolled back
        detail = _redact(
            f"{type(exc).__name__}: {exc}", url if isinstance(url, str) else ""
        )
        print(f"Migration FAILED and rolled back: {detail}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
