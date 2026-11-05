# Tasks: UI Redesign and Ask AI Sheet

**Feature**: `006-ui-redesign`
**Spec**: `.specify/features/006-ui-redesign/spec.md`
**Plan**: `.specify/features/006-ui-redesign/plan.md`
**Status**: Complete — all checklist tasks and automated validation finished

## Rules

- Complete tasks in dependency order; do not begin implementation before the
  authored tests and their failing baseline are explicitly approved.
- Preserve existing copy, authentication, validation, task CRUD, API contracts,
  and Phase I–III behavior.
- Do not read or print `.env` or `.env.local` values. No backend, auth, database,
  MCP, API contract, or environment changes.
- Do not add dependencies, delete files, stage, commit, push, or deploy.
- Use only installed and documented ChatKit options; surface unsupported mockup
  details as limitations rather than modifying ChatKit internals.
- Keep the dashboard "Request failed" investigation read-only and separate from
  redesign implementation.

## Tasks

| Task ID | Description | Preconditions | Expected Outputs | Files | Status |
|---|---|---|---|---|---|
| T001 | Inspect installed ChatKit types and current ChatPanel integration to confirm supported theme/history controls, concrete-height requirements, and persisted conversation resume behavior. Trace the dashboard "Request failed" banner to its source and available non-sensitive logs without changing behavior. | Task list approved. | ChatKit types confirm dark scheme, accent/radius customization, and supported history methods. The SQLModel ChatKit store loads user threads/items from persisted conversations; no live banner logs were present. Frontend source confirms the generic banner fallback when a non-OK response lacks JSON `detail`/`error`; the specific incident cause remains unconfirmed. No files changed. | Read-only inspection | Complete |
| T002 | Write focused failing-first tests for Ask AI trigger visibility, sheet open/close, Escape, backdrop, close control, focus entry/return, dialog semantics, ChatKit endpoint/theme integration, and conversation continuity. Update route/navigation/debug-text tests only where required by the approved behavior. | T001 complete. | Tests encode the new observable behaviors; no production files changed. Identify each changed existing test and why. | `frontend/src/components/__tests__/AskAIWidget.test.tsx` (new); `frontend/src/__tests__/dashboard-chat-link.test.tsx`; `frontend/src/__tests__/chat-page.test.tsx`; `frontend/src/__tests__/chatpanel-jwt.test.tsx` | Complete |
| T003 | Run the authored/adjusted focused tests, confirm failures are for the intended missing behavior, and present the test diff and real failure output for explicit user approval. | T002 complete. | User approved the focused tests after the red run: 4 failed files, 4 failed tests, and 2 passed at the failing-first checkpoint. | Test review gate | Complete; approved |
| T004 | Implement the authenticated dashboard Ask AI trigger and accessible responsive sheet, including keyboard/pointer dismissal, focus management, reduced-motion behavior, and existing ChatPanel integration. Preserve the per-user endpoint, auth, concrete-height mount, and conversation resume behavior. | T003 approved; T001 confirms supported ChatKit behavior. | Dashboard-only Ask AI sheet reuses ChatPanel and supported ChatKit history/theme controls; it remains mounted across close/reopen. | `frontend/src/components/AskAIWidget.tsx` (new); `frontend/src/components/ChatPanel.tsx`; `frontend/src/app/dashboard/page.tsx`; focused frontend tests | Complete |
| T005 | Redirect `/chat` to `/dashboard`, remove the Chat sidebar link, and remove the specified debug status text while preserving meaningful error visibility and existing ChatPanel functionality. | T003 approved. | Legacy route redirects; removed navigation/debug UI is covered by regression tests; files remain present. | `frontend/src/app/chat/page.tsx`; `frontend/src/app/dashboard/page.tsx`; `frontend/src/components/ChatPanel.tsx`; focused frontend tests | Complete |
| T006 | Apply the approved design tokens, typography, responsive layouts, card/button/input/task styling, gradients, and CSS fallbacks to landing, auth, and dashboard surfaces without changing copy or behavior. Use inline SVG/CSS only and self-host Plus Jakarta Sans through `next/font`. | T003 approved. | Shared dark-glass design and self-hosted font applied; no new runtime dependencies or altered form/task behavior. | `frontend/src/app/globals.css`; `frontend/src/app/layout.tsx`; `frontend/src/app/page.tsx`; shared styles used by auth and dashboard | Complete |
| T007 | Run the complete frontend tests, production build, and backend unittest suite. Compare results with the approved task checklist and report actual counts, affected existing tests/reasons, ChatKit limits, banner finding, and unverified manual checks. | T004, T005, and T006 complete. | Frontend 66/66; production build succeeded; backend 194/194. Browser-only checklist remains unverified. | No additional files | Complete |

## Dependencies

| Task ID | Depends on |
|---|---|
| T002 | T001 |
| T003 | T002 |
| T004 | T003 |
| T005 | T003 |
| T006 | T003 |
| T007 | T004, T005, T006 |

T001 is prerequisite inspection. T004, T005, and T006 may proceed independently
after the authored tests and failing baseline receive explicit approval.

## Validation Commands

Run from the repository root in PowerShell:

```powershell
Set-Location frontend; npm test
Set-Location frontend; npm run build
Set-Location ..
uv run python -m unittest discover -s tests
```
