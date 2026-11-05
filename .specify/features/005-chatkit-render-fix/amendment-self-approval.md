# Fast-track amendment note

Fast-track, approved 2026-10-25. This fix follows the MCP contract change in `docs/fix.txt`: verified `user_id` must come from server-side request metadata, logging must redact secrets and write to stderr, and the subprocess path must use the repo `src` import path with a temp SQLite `DATABASE_URL` and explicit timeout.
