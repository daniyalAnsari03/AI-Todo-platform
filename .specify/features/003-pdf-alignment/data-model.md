# Data Model & Migration Plan — 003-pdf-alignment (described only; nothing executes at Plan stage)

Date: 2026-10-24. Every schema change below requires **explicit user approval
before it executes** (spec FR-208). This document is the description the user
approves; execution belongs to the Implement stage, after the Tasks gate.

## 1. Target state — `todo_item` (backend, PostgreSQL)

Current model (`src/todo_app/models.py:78`, table `todo_item`):
`id` PK int · `user_id` FK → `user.id` · `description` TEXT NOT NULL ·
`completed` BOOL.

Target (PDF FR-201–206):

| Column      | Target type / constraint                                       | Change           |
|-------------|----------------------------------------------------------------|------------------|
| id          | serial PK, int                                                 | unchanged        |
| user_id     | TEXT FK → `user.id`, indexed                                   | unchanged        |
| title       | TEXT NOT NULL, 1–200 chars after trim (app-validated; ≤200 DB)  | **NEW**          |
| description | TEXT NULL, ≤1000 chars enforced at API write                    | relaxed to NULL  |
| completed   | BOOL NOT NULL DEFAULT false                                     | unchanged        |
| created_at  | TIMESTAMPTZ NOT NULL (set at creation; never updated after)     | **NEW**          |
| updated_at  | TIMESTAMPTZ NOT NULL (refreshed on every modification)          | **NEW**          |

- DB-level integrity: title length ≤200 / description ≤1000 are enforced
  **application-side** (SQLModel + Pydantic in the router). A DB CHECK is optional
  belt-and-braces; the current codebase enforces validation in the API layer and
  adding CHECKs would widen migration surface for no observable-behavior gain —
  **recommendation: no new CHECK constraints** (rejected alternative noted for
  completeness: `CHECK (char_length(title) BETWEEN 1 AND 200)` etc. — simpler to
  add later if the user wants DB-guaranteed caps).
- Table rename (`todo_item` → `task`):
  **not planned** — the PDF constrains field names and API paths, not table
   renames are pure migration risk (OQ-7 DECIDED — approved by user: keep
   `todo_item`; revisit in Phase III).
- SQLModel declaration after change (`models.py`):
  `title: str`, `description: Optional[str] = None`, `created_at: datetime`,
  `updated_at: datetime` (default-factory pattern per `User.created_at` as today).
- No changes to `user`, `session`, `account`, `verification` tables.
- Fresh databases: `init_db()` (`create_all`) produces the full target schema with
  no migration needed. Pre-existing databases (dev Neon DB) need the migration in
  §3 — `create_all` never ALTERs existing tables, so a migrated DB is required
  before app start against existing data.

## 2. Legacy-row mapping (lossless — spec OQ-1 Option 2, recommended)

Every legacy row (`description` only): after migration,

- `title` = first 200 characters of `description` (Python string slice —
  characters, not bytes; no surrogate splitting concerns for TEXT).
- `description` = the full original text, byte-for-byte. **No truncation,
  no deletion, no reordering.**
- `created_at` = `updated_at` = migration-time timestamp (`now()`), satisfying
  FR-208's backfill requirement and FR-205/206 afterward.
- Over-long legacy `description` (>1000 chars): rows keep their text unmodified —
  the 1000 cap is an API-write validation, not a storage cap on data that already
  exists (protects the no-loss guarantee; OQ-1 recommendation). The API accepts
  only ≤1000 on new/PUT writes.
- Empty/whitespace legacy descriptions: title becomes the trimmed text (may be
  empty-string). Such rows are displayable and can only be re-normalized by later
  edits (API create enforces non-empty titles; migration doesn't change stored
  content). Acceptable per spec (option 2 explicitly tolerates non-obvious
  titles).

Resulting invariant, verified by the migration test: `description.startswith(title)`
unless `len(description) <= 200` and title == description (then equal — still
lossless).

## 3. Migration plan (SQLite tests + one real Postgres run)

Mechanism: a single idempotent migration function
(`src/todo_app/migrations.py::migrate_003` or similar, exact naming at Implement)
executed via a CLI wrapper (e.g. `uv run todo-app-migrate`) or as direct SQL in one
transaction — described steps:

1. **Backup (mandatory gate 1)**: `pg_dump` the Neon DB to a local file outside the
   repo (never committed, respects NFR-001) AND record current row counts per user
   in the migration log. Abort on any failure; `git status` must be clean before
   starting. **Precondition (Correction 2 — clean-git gate):** the repo has no
   commits yet, so the clean-git requirement is satisfied by: **User-authorized
   LOCAL initial commit (no push) before the migration. `.env`/`.env.local` are
   already gitignored. No commit is made without explicit user authorization.**
2. **User-approval gate (mandatory gate 2)**: explicit user go-ahead (OQ-1 option
   + timestamp-backfill choice confirmed) before touching any real DB.
3. In one transaction:
   - `ALTER TABLE todo_item ADD COLUMN title TEXT;`
   - `ALTER TABLE todo_item ADD COLUMN created_at TIMESTAMPTZ;`
   - `ALTER TABLE todo_item ADD COLUMN updated_at TIMESTAMPTZ;`
   - `UPDATE todo_item SET title = SUBSTRING(description FROM 1 FOR 200) ...` —
     i.e. trimmed first ≤200 chars; `description` unchanged;
     `created_at = updated_at = now()` (single `now()` constant for the whole run
     so one migration is one timestamp — trivially reproducible).
   - `ALTER TABLE todo_item ALTER COLUMN description DROP NOT NULL;`
     (description becomes nullable for new empty-description tasks; legacy rows
     are unaffected).
   - Add nothing else (completed stays default-false; indexes unchanged).
4. **Post-condition assertions** inside the migration (fail-fast, roll back on
   violation): every row's `title` non-null; `created_at == updated_at` on
   migrated legacy rows; row count unchanged pre/post.
5. Idempotency guard: detect presence of the `title` column first; skip cleanly
   with a report (running twice changes nothing).

SQLite (test) variant: same column adds; `TIMESTAMPTZ` maps to the standard
`DATETIME` in SQLModel — the tests use SQLModel's schema directly, so the Postgres
SQL script and the test migration function share logic via new-model insertions +
per-column updates (details at Implement; the test in
`tests/test_migration.py` runs the same migration function against SQLite).

## 4. Frontend / Better Auth side (OQ-8 DECIDED — approved by user: Option A/JWKS)

**Option A (JWKS) — chosen** (backup + explicit user approval before any DB
schema change remains mandatory): one new Better Auth-managed table:

```sql
CREATE TABLE jwks (
  id   TEXT PRIMARY KEY,
  public_key  TEXT NOT NULL,
  private_key TEXT NOT NULL,   -- encrypted by Better Auth with the shared BETTER_AUTH_SECRET
  created_at  TIMESTAMP NOT NULL,
  expires_at  TIMESTAMP,       -- NULL unless rotation enabled
  alg  TEXT,                   -- 'RS256' per OQ-8 Option A recommendation
  crv  TEXT
)
```

(fields mirror `frontend/node_modules/better-auth/dist/plugins/jwt/schema.mjs`;
exact column names/types per Better Auth's drizzle conventions at Implement.) Same
approval + backup discipline as §3. Also reflected in
`frontend/src/lib/schema.ts` as a `pgTable("jwks", ...)` so the drizzle adapter
(`frontend/auth.ts`) recognizes it (schema mapping must gain the `jwks` key).

**Option B (HS256 shared-secret sign callback)**: no schema change, no `jwks`
table. **Not chosen** (OQ-8 decided = Option A); kept here only as the
historical record of the rejected alternative.

Either option touches no other Better Auth table; `user`/`session`/`account`/
`verification` remain as-is (JWT plugin requires live sessions for token
issuance).

## 5. Rollback plan

- Postgres `todo_item` changes: restore from the `pg_dump` backup (drop + recreate
  or per-table restore), or run inverse SQL (`ALTER TABLE todo_item DROP COLUMN
  title, created_at, updated_at;` + re-ADD NOT NULL on description after
  temporarily filling derived titles) — the backup restore is primary (cleaner,
  preserves exact pre-migration state including row counts).
- `jwks` table (Option A): `DROP TABLE jwks;` + revert `frontend/auth.ts` plugin
  config and `frontend/src/lib/schema.ts`. No user data in this table.
- Application rollback: revert the commit/branch to the pre-feature state; old
  `/api/items` server code lives in git history. Old code against a migrated DB
  breaks only on the new required columns' absence — that combination
  (rollback code, keep schema) is not planned for; rollback = restore both code
  and DB backup.
- Timestamps in legacy rows are backfilled `now()`, so a complete rollback loses
  only the derived title/description *representation* (original description bytes
  are restored intact by the backup).

## 6. What is NOT changed

- `user`, `session`, `account`, `verification` schemas (including their current
  column names/notes) — untouched.
- Phase I in-memory store: no persistence layer (existing behavior retained);
  the store dataclass gains the same conceptual fields but lives in memory.
- Database technology (Postgres/Neon), connection strings, `.env` handling —
  untouched (`DATABASE_URL` consumed exactly as today; `BETTER_AUTH_SECRET`
  remains configured for the frontend/Better Auth side only, and per Amendment 1
  the backend no longer reads it; NFR-001 respected: migration script reads env,
  never logs secrets).
