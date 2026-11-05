# PostgreSQL driver regression amendment

Fast-track amendment, approved by the user on 2026-10-25. Restore normalization
of `postgresql://` and `postgres://` URLs to the installed Phase II driver
(`psycopg2-binary`); retain SQLite URL behavior. Add a regression test that
checks SQLAlchemy's resolved driver is importable, then verify engine creation
and normal API startup without querying or printing connection details.
