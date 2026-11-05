# Implementation Plan: ChatKit Rendering and Adapter Repair

**Branch**: `005-chatkit-render-fix` | **Date**: 2026-10-25 | **Spec**: `.specify/features/005-chatkit-render-fix/spec.md`

**Input**: User-approved specification for the requested repair in `docs/fix.txt`.

## Summary

Diagnose why the authenticated `/chat` page does not show the ChatKit widget,
then make the smallest frontend or backend changes needed to render it reliably.
Add a visible, token-safe status under the heading, including ChatKit errors.
Verify the same-origin rewrite and test the four required ChatKit protocol
operations using isolated test storage and mocked agent behavior.

## Technical Context

**Language/Version**: TypeScript / React 19 / Next.js 16; Python 3.13+

**Primary Dependencies**: `@openai/chatkit-react`, FastAPI, `openai-chatkit`

**Storage**: Existing application storage is unchanged; endpoint tests use an
isolated in-memory SQLite database and must not access real databases.

**Testing**: Vitest, Next.js production build, and the full unittest suite via uv.

**Target Platform**: Windows-compatible local development; Next.js on port 3000
proxies to FastAPI on port 8000.

**Project Type**: Existing web application (Next.js frontend and FastAPI API).

**Constraints**: No secrets or `.env` values read or printed. Do not modify
todo-item behavior, auth configuration, or dashboard behavior. No staging,
committing, pushing, or deleting. Keep adapter errors explicit; no empty
success-shaped fallbacks.

**Scope**: `ChatPanel.tsx`, its focused tests, the ChatKit API adapter and focused
endpoint tests; Next.js rewrite configuration only if investigation shows it is
incorrect.

## Approved-Scope Amendment Plan

For the newly approved requirements, inspect the installed ChatKit React type
definitions and installed `openai-chatkit` implementation read-only before
choosing API options or adapter call order. Add the frontend concrete-height,
border, and full-size-style assertions. Add a backend `threads.create`
regression test that promotes the un-awaited-coroutine warning to an error,
checks the converted input received by the runner, and checks for an assistant
message item in SSE. Verify the adapter derives MCP tool `user_id` from the
verified request identity, not model input. Show the failing test results before
changing implementation, then run both complete test suites and the frontend
production build.

## Constitution Check

- **Spec-First**: Pass — this plan follows the approved specification.
- **Test-First**: Pass — add/adjust failing frontend and backend tests before
  changing implementation; implementation is gated on approval of the task list.
- **Lifecycle & Review Gates**: Pass — tasks and implementation remain gated on
  explicit user review.
- **Runtime, dependencies, and layout**: Pass — no changes planned to Python
  runtime, uv, build backend, or package layout.
- **Scope discipline**: Pass — preserve dashboard, auth configuration, and task
  behavior; no unrelated refactoring.

## Design and Execution

1. **Frontend tests first**: Extend the focused ChatPanel tests to verify visible
   user-ID presence, token loading/ready/error states, absence of token contents,
   ChatKit rendering after readiness, and display of the ChatKit `onError`
   message. Mock the ChatKit hook and token provider; assert requests still use
   the authenticated token without inspecting/logging its value.
2. **Backend tests first**: Extend the adapter contract tests for
   `threads.create`, `threads.list`, `items.list`, and `threads.get_by_id`.
   Use FastAPI's test client, a stub ChatKit server, mocked external AI behavior,
   and the existing isolated SQLite setup. Assert status, response shape, and
   content type; ensure no test uses real OpenAI credentials or production
   storage.
3. **Implementation**: Trace the token fetch/render path, ChatKit initialization
   and error callback, endpoint result serialization, and Next.js rewrite.
   Change only the path demonstrated to be faulty. Keep token loading and
   failure visible beneath the heading; never render token data. Preserve the
   established authenticated request and route. Return protocol-correct JSON or
   streaming responses for each operation and surface processing/serialization
   failures rather than returning `{}`.
4. **Code-file traceability**: Every modified or created code file must include
   a concise comment linking it to its approved task ID and this plan/spec
   section, as required by the existing feature tasks.
5. **Verification**: Run the full frontend tests, frontend production build, and
   full backend suite. Do not read or print `.env` values.

## Planned Files

```text
.specify/features/005-chatkit-render-fix/
├── spec.md
├── plan.md
└── tasks.md                 # Produced only after Plan approval

frontend/src/components/ChatPanel.tsx
frontend/src/__tests__/chatpanel-jwt.test.tsx
frontend/src/components/__tests__/ChatPanel.test.tsx
src/todo_app/chat/chatkit_server.py
tests/test_chatkit_adapter.py
```

`frontend/next.config.js` is in scope only if inspection or a regression test
shows the existing `/api/:userId/chatkit` rewrite is incorrect.

## Validation Commands

Run from the repository root in PowerShell:

```powershell
Set-Location frontend; npm test
Set-Location frontend; npm run build
Set-Location ..
uv run python -m unittest discover -s tests
```

## Complexity Tracking

No constitution violations or new architectural components are planned.
