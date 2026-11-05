# Feature Specification: UI Redesign and Ask AI Sheet

**Feature Branch**: `006-ui-redesign`
**Created**: 2026-10-25
**Status**: Approved by user on 2026-10-25
**Input**: `docs/fix.txt`

The Ask AI drawer and backdrop remain hidden and non-interactive while closed, with observable DOM state and delayed CSS visibility transitions for close animation.

## Goal

Refresh the landing, authentication, and dashboard interfaces with a consistent
dark glass visual system, and make the existing authenticated ChatKit experience
available through an accessible Ask AI bottom sheet on the dashboard.

## User Scenarios & Testing

### User Story 1 — Use the refreshed application (Priority: P1)

Visitors and authenticated users see a cohesive, responsive redesign on the
landing, login, signup, and dashboard pages while existing copy, validation,
authentication, task operations, and API behavior remain unchanged.

**Independent Test**: Exercise the existing page flows and dashboard task CRUD;
verify the redesigned layouts preserve their behavior and are usable at mobile
and desktop widths.

### User Story 2 — Open and use Ask AI (Priority: P1)

An authenticated dashboard user can open Ask AI, continue using the existing
ChatKit-backed conversation, and close or reopen the sheet without losing the
persisted conversation.

**Independent Test**: Verify the trigger, sheet, ChatKit mount, supported theme,
keyboard and pointer close behavior, focus handling, and conversation resume
using existing authentication and API behavior.

### User Story 3 — Reach the dashboard from the legacy chat route (Priority: P2)

Opening `/chat` redirects to `/dashboard`; the dashboard no longer exposes a
Chat sidebar link or debug token/user status text.

**Independent Test**: Verify the redirect and absence of the removed link and
debug text in the authenticated UI.

## Functional Requirements

- **FR-001**: The landing, login, signup, and dashboard pages MUST adopt the
  approved dark glass visual design while preserving existing content,
  validation, authentication, task behavior, and API calls.
- **FR-002**: The visual system MUST use centralized CSS variables for the
  specified colors, gradients, borders, radii, shadows, and typography. Cards
  MUST provide a solid-color fallback when backdrop filtering is unavailable.
- **FR-003**: The dashboard MUST retain its Overview/Home/logout navigation,
  user chip, task statistics, task creation, and task row actions, with the
  specified visual treatment.
- **FR-004**: The authenticated dashboard MUST provide a fixed, accessible
  Ask AI trigger that opens a responsive bottom sheet containing the existing
  Phase III ChatKit component.
- **FR-005**: The sheet MUST use the existing authenticated ChatKit token,
  `/api/{user_id}/chatkit` adapter, and persistence. It MUST NOT change backend,
  auth, database schema, MCP, API contract, or environment configuration.
- **FR-006**: ChatKit MUST retain its concrete-height wrapper and block/full-size
  mounting requirements. Only ChatKit theme options supported by the installed
  package may be used.
- **FR-007**: The sheet MUST have dialog semantics, move focus into the dialog
  when opened, return focus to the trigger when closed, and close with Escape,
  its close control, or backdrop activation. Its open/close motion MUST respect
  reduced-motion preferences.
- **FR-008**: Closing and reopening the sheet MUST preserve access to the
  existing database-backed conversation.
- **FR-009**: `/chat` MUST redirect to `/dashboard`; the Chat sidebar link and
  debug text "User ID: present; Token: ready" MUST be removed.
- **FR-010**: Inline SVG icons and CSS-only gradients MUST be used; no new
  dependency or third-party brand asset may be introduced.
- **FR-011**: Tests MUST cover Ask AI open/close, Escape, backdrop, focus,
  accessibility attributes, `/chat` redirect, and removal of the sidebar link.
  Existing tests may change only where the approved behavior makes them
  obsolete.
- **FR-012**: Validation MUST include the complete frontend test suite, frontend
  production build, and backend unittest suite.

## Design Decisions

- Application base: `#0A0B18`; primary text: `#F3F1FA`; secondary text:
  `#A9A7B8`.
- Main panel: `linear-gradient(180deg, #111530 0%, #3A2D4F 45%, #07070F 100%)`,
  1px translucent white border, 24px radius.
- Glass cards: translucent white fill and border, 16–18px radius, soft shadow,
  and backdrop blur with a solid fallback.
- Primary/active navigation gradient: `#4B2189` to `#2E1457`, `#7B4BD6`
  border, 16px radius. Add/Send gradient: `#5B2D9E` to `#2E1457`.
- Inputs: `#1F2230` fill, translucent white border, `#7C7B8C` placeholder,
  16px radius. Danger accent: `#F2A0B5`.
- Logo mark: CSS gradient `#6D3BF2` to `#3B1FA8`. Progress card:
  `rgba(123,75,214,0.45)` to `rgba(75,33,137,0.35)`, `#7B4BD6` border.
- Use self-hosted Plus Jakarta Sans via `next/font`; no CDN.
- Ask AI trigger: 52px fixed bottom-right circle with the specified radial
  gradient, soft glow, sparkles icon, and accessible name "Ask AI".
- Ask AI sheet: full width, approximately 46vh height, clamped to at least
  320px and at most 70vh, 28px top corners, handle, header, orb, history and
  close controls, dimmed backdrop, and slide-up animation.
- ChatKit styling is limited to supported theme options (dark color scheme,
  accent, and radius); unsupported mockup details MUST NOT be implemented by
  modifying ChatKit internals.

## Scope Boundaries

- Preserve Phases I–III behavior, all existing copy, validation, API calls, and
  authenticated conversation persistence.
- Do not change backend, authentication/JWT/JWKS, database schema, MCP, API
  contract, or environment files.
- Do not add dependencies, delete files, stage, commit, push, or deploy.
- Investigate the dashboard's "Request failed" banner read-only and report the
  confirmed cause separately; do not fix it unless the cause is purely styling.
- Manual browser checks remain outside automated verification and must be
  reported as unverified unless actually performed.

## Amendment (2026-10-26)

The dashboard uses a full-viewport shell with a 240px unboxed sidebar and a
scrolling, bordered main panel; mobile layouts replace the sidebar with an
accessible top-bar menu. The task form is a single input row, task rows include
a completion tick control, and public/auth pages use responsive glass layouts.
Ask AI is a full-height right-side drawer (full-width on mobile), replacing the
previous bottom sheet; its ChatKit conversation remains mounted across close
and reopen. Add staggered, interactive CSS motion and reduced-motion support.
All pages must avoid horizontal overflow and reflow for mobile, tablet, and
desktop widths.

## Acceptance Criteria

- **AC-001**: All four specified application areas use the shared responsive
  visual system without changing existing user-visible copy or behavior.
- **AC-002**: Ask AI is available only to authenticated users and opens the
  existing ChatKit experience in a responsive, accessible sheet.
- **AC-003**: Escape, backdrop, and close control dismiss the sheet; focus
  enters on open and returns to the trigger on close.
- **AC-004**: Reopening the sheet resumes the user's persisted conversation;
  no backend or persistence contract changes are required.
- **AC-005**: `/chat` redirects to `/dashboard`, and the Chat sidebar link and
  debug status text are absent.
- **AC-006**: Focused new/updated tests demonstrate the requested behaviors;
  the full frontend suite, frontend build, and backend suite pass.
- **AC-007**: The final report identifies changed files, failing-first test
  evidence, actual test counts, build outcome, modified existing tests and
  reasons, ChatKit styling limitations, the separate banner finding, and
  unverified manual scenarios.
