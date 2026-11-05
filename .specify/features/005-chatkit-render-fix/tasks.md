# Tasks: ChatKit Rendering and Adapter Repair

**Feature**: 005-chatkit-render-fix  
**Spec**: `.specify/features/005-chatkit-render-fix/spec.md`  
**Plan**: `.specify/features/005-chatkit-render-fix/plan.md`  
**Status**: Complete — amendment tests approved and all amendment tasks finished.

## Rules

- Windows/PowerShell-compatible commands.
- Do not read or print `.env` values; do not use real OpenAI credentials or
  production storage.
- Do not change todo-item behavior, auth configuration, or dashboard behavior.
- Do not stage, commit, push, or delete files.
- Tests must be written first and explicitly approved before implementation.
- Every modified or created code file must contain a concise comment linking it
  to its task ID and the relevant spec/plan section.

## Tasks

| Task ID | Description | Preconditions | Expected Outputs | Files | Status |
|---|---|---|---|---|---|
| T8101 | Trace the ChatPanel token/render flow, ChatKit initialization/error path, adapter response handling, and existing Next.js rewrite; record the evidence-based root cause and exact minimal fix. | Task list approved. | Rewrite and JWT endpoint were correct; token failures were hidden by early returns/redirects, ChatKit errors were unhandled, and adapter serialization failures became empty HTTP 200 responses. | Read-only investigation | Complete |
| T8102 | Add frontend tests for visible user-ID and token lifecycle status, ChatKit rendering after token readiness, token secrecy, and displayed `onError` messages. | Task list approved. | Focused tests exercise the approved UI contract and fail where current behavior violates it. | `frontend/src/__tests__/chatpanel-jwt.test.tsx` | Complete; user-approved |
| T8103 | Add adapter contract tests for `threads.create`, `threads.list`, `items.list`, and `threads.get_by_id`, checking response status, shape, and content type with stubbed ChatKit/AI and isolated test storage. | Task list approved. | Four-operation contract coverage and a regression test for serialization errors; tests do not call OpenAI or production storage. | `tests/test_chatkit_adapter.py` | Complete; user-approved |
| T8104 | Present the authored tests and results for explicit user approval; do not alter production code before approval. | T8102 and T8103 complete. | User-approved tests and recorded expected failing baseline. | Review gate | Complete; approved |
| T8105 | Apply the smallest evidence-based frontend and/or adapter fix; preserve authenticated requests, show visible token-safe status and ChatKit errors, and return correct protocol responses without silent empty fallbacks. | T8101 complete; T8104 approved. | ChatKit renders when ready; failures are visible; tested operations return valid responses. | `frontend/src/components/ChatPanel.tsx`; `src/todo_app/api/chatkit.py`; `frontend/next.config.js` only if T8101 proves it faulty | Complete |
| T8106 | Run all required validation and report root cause, changed files, test counts, and exact restart commands. | T8105 complete. | Frontend 60/60, build successful, backend 185/185. | No additional files | Complete |
| T8107 | Add frontend sizing regression coverage and a backend `threads.create` regression test for the awaited conversion, converted runner input, assistant SSE item, and absence of never-awaited warnings; verify installed package APIs and server-side verified-user injection read-only. | Amendment task list approved. | New tests fail on current behavior and do not permit model-selected MCP `user_id`. | `frontend/src/__tests__/chatpanel-jwt.test.tsx`; `frontend/src/components/__tests__/ChatPanel.test.tsx`; `tests/test_chatkit_adapter.py` | Complete; failing baseline recorded |
| T8108 | Present failing regression results and authored tests for explicit user approval; do not alter production code before approval. | T8107 complete. | User-approved tests and recorded failing baseline. | Review gate | Complete; approved |
| T8109 | Fix the ChatKit wrapper sizing and adapter async streaming call sequence using only verified installed APIs; preserve server-side identity injection and MCP lifecycle. | T8108 approved. | Frontend wrapper has concrete visible dimensions; adapter uses the installed Runner signature and AgentContext, with attached MCP servers connected through streaming. | `frontend/src/components/ChatPanel.tsx`; `src/todo_app/chat/chatkit_server.py`; `src/todo_app/chat/runner.py` | Complete |
| T8110 | Run complete backend and frontend suites plus frontend production build; report both root causes, changed files, and actual test counts. | T8109 complete. | Required suites/build pass and actual counts are reported. | No additional files | Complete — backend 187/187; frontend 61/61; build successful |

## Dependencies

| Task ID | Depends on |
|---|---|
| T8104 | T8102, T8103 |
| T8105 | T8101, T8104 |
| T8106 | T8105 |

T8101, T8102, and T8103 are otherwise independent.
T8108 depends on T8107; T8109 depends on T8108; T8110 depends on T8109.

## Validation Commands

Run from the repository root in PowerShell:

```powershell
Set-Location frontend; npm test
Set-Location frontend; npm run build
Set-Location ..
uv run python -m unittest discover -s tests
```
