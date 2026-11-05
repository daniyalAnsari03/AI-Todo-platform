# Implementation Plan: UI Redesign and Ask AI Sheet

**Branch**: `006-ui-redesign` | **Date**: 2026-10-25
**Spec**: `.specify/features/006-ui-redesign/spec.md`
**Status**: Approved by user on 2026-10-25

## Summary

Apply the approved dark-glass design through the existing global stylesheet and
page/component markup, preserving the app's existing copy and behaviors. Replace
the standalone `/chat` page with a redirect and provide the existing ChatKit
panel through an authenticated dashboard Ask AI sheet. No backend or persistence
changes are planned.

## Technical Context

**Frontend**: TypeScript, React 19, Next.js 16, App Router.
**Chat**: Existing `@openai/chatkit-react` 1.6.x component and
`/api/{user_id}/chatkit` endpoint; no new dependency planned.
**Styles**: Existing shared `frontend/src/app/globals.css`; `next/font` is
available through Next.js for self-hosted font delivery.
**Tests**: Vitest and Testing Library; existing suite is in
`frontend/src/**/__tests__`.
**Backend**: Python/FastAPI, unchanged; full unittest suite is a regression
check only.
**Constraints**: Preserve all current copy, auth, validation, CRUD, API and
database behavior. Do not read or print environment values. Do not stage,
commit, push, deploy, delete files, or add dependencies.

## Constitution Check

- **Spec-First**: Pass — the specification was explicitly approved before this
  plan.
- **Test-First**: Required — author focused failing tests and present their
  results for explicit approval before production changes.
- **Lifecycle & Review Gates**: Pass — task generation and implementation each
  remain blocked on their respective approvals.
- **Runtime, dependencies, and layout**: Pass — no backend stack or package
  layout changes; no new dependency planned.
- **Scope discipline**: Pass — preserve Phases I–III behavior and treat the
  dashboard error banner as a separate, read-only investigation.

## Design and Execution

1. **Confirm integration constraints**: Read installed ChatKit React type
   declarations and existing panel implementation to confirm supported theme,
   history, and mounting options. Trace how ChatKit resumes a user's
   persisted conversation. Do not use undocumented internals.
2. **Write focused tests first**:
   - Extend dashboard/page tests to cover an authenticated Ask AI trigger,
     opening and closing the sheet, dialog attributes, Escape, backdrop,
     close control, and focus entry/return.
   - Verify the existing ChatKit panel is mounted inside the sheet with its
     per-user endpoint and supported dark theme options, and remains resumable
     after close/reopen.
   - Update the legacy `/chat` tests to assert the dashboard redirect and
     update the dashboard navigation test to assert no Chat link.
   - Add focused visual-contract assertions only where stable and relevant;
     do not test CSS constants as a substitute for user-visible behavior.
   Run the focused tests and record the intended failures. Present the tests
   and failure output for user approval before implementation.
3. **Implement the Ask AI surface**: Add a focused client-side dashboard widget
   for trigger, backdrop, sheet, keyboard dismissal, and focus management.
   Reuse `ChatPanel` and its existing authenticated token/adapter wiring.
   Preserve ChatKit mounting dimensions; keep the conversation available across
   sheet close/reopen and verify resume behavior against existing code/tests.
   Apply only ChatKit options supported by installed types. If the requested
   history control or mockup styling is unsupported, retain ChatKit's supported
   UI and report that limit rather than hacking internals.
4. **Implement route and navigation changes**: Replace `/chat` page behavior
   with a redirect to `/dashboard`; remove only the Chat sidebar link and the
   specified debug status text. Do not delete the route or ChatPanel files.
5. **Restyle existing surfaces**: Centralize design tokens and shared glass
   surfaces in `globals.css`; load Plus Jakarta Sans using `next/font`; restyle
   landing, auth forms, dashboard/sidebar, stats, task form/rows, and responsive
   states. Preserve existing text, labels, validation and event handlers. Use
   inline SVGs/CSS gradients only.
6. **Separate banner investigation**: Trace the existing "Request failed"
   message through frontend API error handling and relevant source/configuration.
   Use available read-only logs if present, do not expose secrets, make no
   behavior fix, and report confirmed evidence separately from hypotheses.
7. **Verification**: Run the complete frontend test suite, production build,
   and backend unittest suite with the commands requested in `docs/fix.txt`.
   Report actual counts, build outcome, modified legacy tests and reasons, known
   ChatKit limits, the separate banner finding, and unverified browser checks.

## Planned Files

```text
.specify/features/006-ui-redesign/
├── spec.md
├── plan.md
└── tasks.md                       # Created only after Plan approval

frontend/src/app/globals.css       # Shared tokens, responsive visual system
frontend/src/app/layout.tsx        # Self-hosted font setup
frontend/src/app/page.tsx          # Landing-page visual structure as needed
frontend/src/app/login/page.tsx    # Only if auth layout needs page-level changes
frontend/src/app/register/page.tsx # Only if auth layout needs page-level changes
frontend/src/app/dashboard/page.tsx
frontend/src/app/chat/page.tsx     # Redirect; retain file
frontend/src/components/AuthForm.tsx
frontend/src/components/TodoList.tsx
frontend/src/components/ChatPanel.tsx
frontend/src/components/AskAIWidget.tsx # New client-side trigger/sheet
frontend/src/**/__tests__/*        # Focused tests; only affected existing tests
```

The exact code-file list will be narrowed in the task checklist after test and
ChatKit API inspection. No backend, auth, database, MCP, API-contract, or
environment files are in scope.

## Validation Commands

From the repository root in PowerShell:

```powershell
Set-Location frontend; npm test
Set-Location frontend; npm run build
Set-Location ..
uv run python -m unittest discover -s tests
```

## Complexity Tracking

One focused client widget is the only planned new runtime component. No new
dependencies, backend changes, or persistence mechanisms are required.
