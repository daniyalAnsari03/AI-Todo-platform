# Todo App

## Run the app

Backend:

```bash
uv run --env-file .env todo-app-api
```

Frontend:

```bash
cd frontend
npm run dev
```

Phase I CLI:

```bash
uv run todo-app
```

Supported commands:

- `add <title> | <description>`
- `update`
- `toggle`
- `complete`
- `list`
- `delete`
- `help`

## Environment variables

## Phase III: AI Todo Chatbot

### Setup and configuration

Prerequisites: Python 3.13 or newer with `uv`, Node.js with npm, a PostgreSQL/Neon
database, Better Auth configuration, and an OpenAI API key.

Configure these backend variable names in `.env` (names only):

```text
DATABASE_URL
BETTER_AUTH_URL
JWT_JWKS_URL
JWT_ISSUER
JWT_AUDIENCE
BETTER_AUTH_SECRET
OPENAI_API_KEY
OPENAI_MODEL
```

`NEXT_PUBLIC_OPENAI_DOMAIN_KEY` is needed only for production-hosted ChatKit.

Create the chat tables by reviewing the dry run and then applying the migration:

```powershell
uv run --env-file .env python -m todo_app.migrations --dry-run create-chat-tables
uv run --env-file .env python -m todo_app.migrations create-chat-tables
```

Start the backend from the repository root:

```powershell
uv run --env-file .env todo-app-api
```

Start the frontend in a second terminal:

```powershell
Set-Location frontend
npm run dev
```

Sign in and open `/chat`. Example natural-language requests:

- “Add a task to pay bills.”
- “List my tasks.”
- “Mark the meeting task complete.”
- “Rename the meeting task to Sprint review.”
- “Delete the meeting task.”

### Tests

Run the backend and frontend tests from the repository root:

```powershell
uv run python -m unittest discover tests
Set-Location frontend
npm test
```

## Environment variables (Phase I/II placeholders)

```env
DATABASE_URL=postgresql://user:password@host:5432/dbname
BETTER_AUTH_SECRET=replace-with-stable-secret
BETTER_AUTH_URL=http://localhost:3000
JWT_JWKS_URL=http://localhost:3000/api/auth/jwks
JWT_ISSUER=http://localhost:3000
JWT_AUDIENCE=todo-app
```

## Authentication

The PDF says the backend verifies JWTs with the shared secret `BETTER_AUTH_SECRET`, but the installed `better-auth` 1.7.5 JWT plugin supports asymmetric signing only. By user decision (Amendment 1, OQ-8 = A), the backend verifies tokens via the plugin's JWKS public key using RS256.

Goals remain unchanged:

- stateless verification
- `user_id` in the URL must match the token user
- `401` on invalid token
- per-user isolation

## Release notes

Breaking changes:

- Cookie auth was retired.
- `/api/items` was removed.
- New endpoints are available under `/api/{user_id}/tasks`:
  - `GET /api/{user_id}/tasks`
  - `POST /api/{user_id}/tasks`
  - `GET /api/{user_id}/tasks/{task_id}`
  - `PUT /api/{user_id}/tasks/{task_id}`
  - `DELETE /api/{user_id}/tasks/{task_id}`
  - `PATCH /api/{user_id}/tasks/{task_id}/complete`
- Tasks now include `title`, optional `description`, `created_at`, and `updated_at`.
- The CLI gained `update` and `toggle` commands.
