# Feature Specification: Session-Aware Landing Page

**Feature Branch**: `007-session-aware-landing`

**Created**: 2026-11-04

**Status**: Approved (2026-11-04)

**Input**: `docs/fix.txt` (specify stage only)

## Goal

Make the public landing page at `/` session-aware so authenticated visitors see
a direct path to the dashboard, while unauthenticated visitors keep the current
public landing experience. Authenticated visitors who open `/login` or
`/register` are redirected to `/dashboard` at the page level using the existing
session lookup. The existing session guard, session cookie, token handling,
logout flow, authentication mechanism, backend, and database MUST NOT change.

## User Scenarios & Testing

### User Story 1 - Reach the dashboard from the landing page (Priority: P1)

An authenticated visitor who returns to `/` sees Dashboard navigation and a hero
call to action that lead directly to `/dashboard`, instead of being offered
Login and Get Started.

**Why this priority**: This is the reported defect. Authenticated users currently
see authentication entry points even though a valid session already exists,
which creates an unnecessary login loop.

**Independent Test**: Render the landing page with an authenticated session and
verify that Login and Get Started are absent, a link labeled Dashboard targets
`/dashboard` in both desktop and mobile navigation, and the hero primary CTA is
labeled "Go to Dashboard" and targets `/dashboard`.

**Acceptance Scenarios**:

1. **Given** a valid session, **When** an authenticated visitor loads `/`, **Then**
   the navigation shows a link labeled Dashboard whose target is `/dashboard` and
   does not show Login or Get Started.
2. **Given** a valid session and a mobile viewport, **When** the visitor opens the
   landing mobile menu, **Then** the mobile navigation also shows a link labeled
   Dashboard targeting `/dashboard` and does not show Login or Get Started.
3. **Given** a valid session, **When** the authenticated visitor loads `/`, **Then**
   the hero primary CTA is labeled "Go to Dashboard" and targets `/dashboard`
   instead of `/register`.
4. **Given** a valid session, **When** the visitor activates the Dashboard link or
   the "Go to Dashboard" CTA, **Then** `/dashboard` opens without any login prompt
   and the existing dashboard content is shown.

---

### User Story 2 - Keep the public landing experience (Priority: P1)

An unauthenticated visitor sees the existing public landing page and authentication
entry points unchanged.

**Why this priority**: The landing page must remain publicly accessible and must
not require or imply a session. Existing unauthenticated conversion paths must be
preserved.

**Independent Test**: Render the landing page with no session and verify that it
renders successfully without redirecting, with Login targeting `/login`, Get
Started targeting `/register`, and the hero primary CTA targeting `/register`.

**Acceptance Scenarios**:

1. **Given** no session, **When** a visitor loads `/`, **Then** the landing page
   renders successfully and does not redirect to `/login`.
2. **Given** no session, **When** the visitor views the desktop or mobile
   navigation, **Then** Login targets `/login`, Get Started targets `/register`,
   and no Dashboard link replaces them.
3. **Given** no session, **When** the visitor loads `/`, **Then** the hero primary
   CTA targets `/register`.

---

### User Story 3 - Skip authentication pages when already signed in (Priority: P1)

An authenticated visitor who opens `/login` or `/register` is sent directly to
`/dashboard` instead of being shown an authentication form for a session they
already have.

**Why this priority**: Authenticated users manually reaching the auth pages
otherwise see a redundant login or registration form, which is confusing and can
lead to an unnecessary login loop.

**Independent Test**: Visit `/login` and `/register` with a valid session and
verify that each redirects to `/dashboard`; visit them without a session and
verify that each still renders its form.

**Acceptance Scenarios**:

1. **Given** a valid session, **When** an authenticated visitor opens `/login`,
   **Then** they are redirected to `/dashboard` and the login form is not shown.
2. **Given** a valid session, **When** an authenticated visitor opens `/register`,
   **Then** they are redirected to `/dashboard` and the registration form is not
   shown.
3. **Given** no session, **When** a visitor opens `/login` or `/register`, **Then**
   the corresponding form is shown normally and no redirect occurs.
4. **Given** a session lookup failure while opening `/login` or `/register`,
   **Then** the form is shown without redirecting and without crashing.

---

### User Story 4 - Preserve session lifecycle behavior (Priority: P2)

Session state on the landing page follows the existing session lifecycle: it is
present while the session is valid and disappears only after explicit logout or
natural expiry.

**Why this priority**: Session-aware rendering must not create a parallel session
model or keep stale authenticated navigation after the session ends.

**Independent Test**: Load `/` with a valid session, then simulate logout and
natural expiry, and verify that the landing page reverts to the unauthenticated
navigation and CTA targets.

**Acceptance Scenarios**:

1. **Given** an authenticated visitor, **When** they explicitly log out and then
   load `/`, **Then** the landing page shows Login, Get Started, and the
   `/register` hero CTA.
2. **Given** an authenticated visitor whose session has expired, **When** they
   load `/`, **Then** the landing page shows the unauthenticated state.
3. **Given** an authenticated visitor with a valid session, **When** they visit
   `/` again after logging in, **Then** the authenticated state is shown without
   requiring another login.

---

### Edge Cases

- A missing, malformed, invalid, or expired session cookie MUST be treated as
  unauthenticated and MUST NOT prevent the landing page from rendering.
- A session lookup failure MUST NOT redirect the visitor to `/login` and MUST NOT
  block the public landing page. The page MUST fall back to the unauthenticated
  presentation; any diagnostic detail belongs in server-side logging only.
- Opening `/dashboard` directly without a valid session MUST continue to redirect
  to `/login` through the existing `requireSession` behavior.
- Session changes in another tab are not required to update an already-rendered
  landing page in real time; the correct state MUST be shown on the next load or
  navigation.
- The existing footer Dashboard link is not part of this feature's required
  behavior and MUST remain unaffected.

## Requirements

### Functional Requirements

- **FR-001**: The landing page at `/` MUST determine the visitor's current
  session state using the existing session mechanism before rendering
  session-dependent navigation and call-to-action elements.
- **FR-002**: For an authenticated visitor, the desktop landing navigation MUST
  show a link labeled Dashboard targeting `/dashboard` in place of Login and Get
  Started.
- **FR-003**: For an authenticated visitor, the mobile landing navigation MUST
  show a link labeled Dashboard targeting `/dashboard` in place of Login and Get
  Started.
- **FR-004**: For an authenticated visitor, the hero primary CTA MUST be labeled
  "Go to Dashboard" and target `/dashboard` instead of `/register`, and the
  navigation entry MUST be labeled "Dashboard". Unauthenticated copy remains
  unchanged as specified in FR-005.
- **FR-005**: For an unauthenticated visitor, the landing navigation MUST continue
  to show Login targeting `/login` and Get Started targeting `/register`, and the
  hero primary CTA MUST continue to target `/register`.
- **FR-006**: The landing page MUST remain publicly accessible for unauthenticated
  visitors and MUST NOT redirect `/` to `/login`.
- **FR-007**: Activating Dashboard with a valid session MUST open `/dashboard`
  without any login prompt. The existing `requireSession` guard MUST continue to
  enforce access to the dashboard.
- **FR-008**: Session-aware rendering MUST reflect only the existing session
  lifecycle. The authenticated landing state MUST end on explicit logout or
  natural session expiry, and the feature MUST NOT introduce client-side
  persistent auth state that outlives the session.
- **FR-009**: The feature MUST NOT change `requireSession`, session retrieval,
  token handling, JWT/JWKS behavior, the logout flow, `auth-handler`, Better Auth
  configuration, cookie configuration, backend behavior, or the database. The
  authenticated-visitor redirects in FR-014 MUST reuse the existing `getSession`
  lookup as a read-only page-level check and MUST NOT alter any authentication
  mechanism.
- **FR-010**: The feature MUST NOT introduce new runtime dependencies, new routes,
  or new authentication mechanisms. The redirects in FR-014 MUST be implemented
  within the existing `/login` and `/register` pages.
- **FR-011**: Existing user-visible landing content, layout, and visual design MUST
  be preserved except for the session-dependent navigation, CTA label, and CTA
  destination changes required above.
- **FR-012**: Automated tests MUST cover authenticated and unauthenticated states
  for desktop navigation, mobile navigation, hero CTA labeling and targeting,
  public landing rendering, reversion after session end, and the `/login` and
  `/register` redirect behavior.
- **FR-013**: Validation MUST include the complete frontend test suite and the
  frontend production build. The existing backend and Phase I CLI suites MUST
  remain untouched and passing.
- **FR-014**: An authenticated visitor who opens `/login` or `/register` MUST be
  redirected to `/dashboard` at the page level using the existing `getSession`.
  This MUST NOT change Better Auth configuration, `auth-handler`,
  `requireSession`, cookies, or token handling.
- **FR-015**: An unauthenticated visitor who opens `/login` or `/register` MUST
  still see the corresponding form normally and MUST NOT be redirected.
- **FR-016**: If the session lookup for the `/login` or `/register` redirect
  check fails, the page MUST fall back to showing the form, with no redirect loop
  and no crash.

### Key Entities

- **Session**: The existing server-side session state used to determine whether a
  visitor is authenticated. This feature reads it but does not add, alter, or
  persist new session data.
- **Landing navigation and CTA state**: The presentation choice between
  authenticated links (Dashboard) and unauthenticated links (Login, Get Started,
  `/register`). No new persistent entity is introduced.

## Acceptance Criteria

- **AC-001**: With a valid session, `/` shows a link labeled Dashboard targeting
  `/dashboard` in both desktop and mobile navigation, and shows neither Login nor
  Get Started.
- **AC-002**: With a valid session, the `/` hero primary CTA is labeled
  "Go to Dashboard" and targets `/dashboard`.
- **AC-003**: With a valid session, activating Dashboard opens `/dashboard`
  without a login prompt and displays the existing dashboard.
- **AC-004**: Without a session, `/` renders without redirecting, Login targets
  `/login`, Get Started targets `/register`, and the hero primary CTA targets
  `/register`.
- **AC-005**: After explicit logout or natural session expiry, `/` shows the
  unauthenticated navigation and CTA targets.
- **AC-006**: A missing, invalid, expired, or unreadable session does not cause a
  redirect or a failed landing-page render.
- **AC-007**: Direct access to `/dashboard` without a session still redirects to
  `/login`.
- **AC-008**: All existing 70 frontend tests continue to pass, and new focused
  tests demonstrate the behaviors in AC-001 through AC-013.
- **AC-009**: The frontend production build succeeds.
- **AC-010**: No changes are made to the Phase I CLI, backend, database schema,
  auth guard, token handling, logout flow, `auth-handler`, Better Auth
  configuration, or cookie configuration.
- **AC-011**: With a valid session, opening `/login` redirects to `/dashboard`
  and the login form is not shown.
- **AC-012**: With a valid session, opening `/register` redirects to `/dashboard`
  and the registration form is not shown.
- **AC-013**: Without a session, `/login` and `/register` render their forms
  normally; if the session lookup fails, the form is still shown with no redirect
  loop and no crash.

## Regression Protection

- The existing 70 frontend tests MUST still pass. Tests may be modified only where
  this approved spec makes their current assertions obsolete; any such change MUST
  be reported with its reason.
- New tests MUST fail before implementation and pass afterward, following the
  project's red-green-refactor requirement.
- The Phase I CLI MUST remain untouched and its tests MUST still pass.
- The backend MUST remain untouched and its full test suite MUST still pass.
- Existing authentication behavior for `/logout` and `/dashboard` MUST remain
  unchanged. `/login` and `/register` behavior is amended only for authenticated
  visitors, who are redirected to `/dashboard`; their unauthenticated behavior is
  unchanged.
- The change MUST NOT touch the real database, secrets, environment files, or git
  state.

## Manual Verification Checklist

Required before the feature is called complete:

- [ ] Log in with an existing account, go to `/`, and confirm the Dashboard link
  and the "Go to Dashboard" CTA are shown while Login and Get Started are absent,
  at both desktop and mobile width.
- [ ] Click Dashboard and confirm the dashboard opens with no login prompt.
- [ ] While logged in, manually visit `/login` and `/register` and confirm each
  redirects to `/dashboard`.
- [ ] Close and reopen the browser tab, visit `/`, and confirm the authenticated
  state is still shown.
- [ ] Log out, visit `/`, and confirm Login/Get Started and "Get Started Free" are
  back, and that `/dashboard` redirects to `/login`.

## Out of Scope

- Moving `nextCookies()` to be the last plugin in `frontend/auth.ts`. This is
  deferred (see Decisions) and would be handled as a separate future feature.
- Any change to `requireSession`, session retrieval, token/JWT/JWKS handling,
  logout, `auth-handler`, Better Auth plugins, or cookie configuration.
- Any backend, database, schema, API contract, MCP, or ChatKit change.
- Any visual redesign, new landing sections, new marketing copy, or dependency
  addition.
- Real-time session synchronization across tabs, client-side polling, or session
  refresh changes.
- Redirecting unauthenticated visitors from `/` to `/login`.
- Changing the existing footer Dashboard link or other unrelated links.
- Updating the prior contract or spec files themselves; this spec records the
  relationship but the specify stage creates only this file.

## Relationship to Prior Artifacts

- **`002-full-stack-todo/contracts/pages.md` (GET / behavior): AMENDS.** That
  contract predates the public landing page and states that an authenticated GET
  `/` renders the todo list while an unauthenticated GET `/` redirects to
  `/login`. The current system, established by the later UI redesign, serves a
  public landing page at `/` and the authenticated todo experience at
  `/dashboard`. This feature further amends the GET `/` behavior to be
  session-aware: `/` stays public in both states; authenticated visitors see
   Dashboard affordances; unauthenticated visitors keep Login/Get Started. The
   `/login` and `/register` behavior is amended for authenticated visitors only:
   they are redirected to `/dashboard` at the page level. `/logout` and
   `/dashboard` behaviors in that contract are not amended by this feature.
- **`006-ui-redesign`: COMPLEMENTS.** This feature does not amend the UI redesign.
  It preserves the redesigned landing page's visual system, layout, and
  unauthenticated copy, and only adds session-dependent navigation and CTA labels
  and destinations. It also amends `/login` and `/register` for authenticated
  visitors only, as noted above. Ask AI, the dashboard, and all authentication
  mechanisms remain as specified by 006.

## Decisions

Decided 2026-11-04.

1. **Redirect authenticated visitors from `/login` and `/register` to
   `/dashboard`: YES.** Approved and included in this spec as FR-014, FR-015, and
   FR-016, User Story 3, AC-011 through AC-013, and SC-007. The redirect is a
   page-level check using the existing `getSession`; it does not change Better Auth
   configuration, `auth-handler`, `requireSession`, cookies, or token handling.
   Unauthenticated visitors still see `/login` and `/register` normally, and a
   session lookup failure falls back to showing the form.
2. **Move `nextCookies()` to be the last plugin in `frontend/auth.ts`: DEFER.**
   Kept out of scope as a separate future feature. If pursued, it must be
   specified and implemented separately with its own regression tests for session
   cookie issuance.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An authenticated visitor loading `/` sees a Dashboard-labeled
  destination in 100% of desktop and mobile navigation checks plus a hero CTA
  labeled "Go to Dashboard", and sees no Login or Get Started entry point.
- **SC-002**: An unauthenticated visitor sees the existing Login, Get Started, and
  `/register` hero CTA behavior with zero redirects away from `/`.
- **SC-003**: Clicking Dashboard with a valid session reaches `/dashboard` with
  zero login prompts in automated and manual checks.
- **SC-004**: After logout or expiry, the landing page shows the unauthenticated
  state on the next load with zero stale Dashboard affordances.
- **SC-005**: All 70 pre-existing frontend tests plus the new focused tests pass,
  and the frontend production build succeeds.
- **SC-006**: The backend test suite and Phase I CLI tests remain unchanged and
  passing, with zero modifications to protected auth, backend, or database files.
- **SC-007**: An authenticated visitor opening `/login` or `/register` reaches
  `/dashboard` with zero auth forms shown; an unauthenticated visitor still sees
  each form with zero redirects.

## Assumptions

- The existing session cookie and `getSession`/`requireSession` behavior are
  correct and must be reused without modification, as confirmed by the diagnosis.
- The landing page can determine session state server-side using the existing
  session mechanism without adding dependencies or changing authentication.
- The landing page remains public; only its session-dependent links, CTA labels,
  and CTA targets change.
- Unauthenticated landing copy is retained, including "Get Started Free", "Login",
  and "Get Started". For authenticated visitors, the nav entry label is "Dashboard"
  and the hero CTA label is "Go to Dashboard"; the previous authenticated copy is
  not preserved.
- The "70 frontend tests" figure is the accepted regression baseline for this
  feature.
- As decided, authenticated visitors are redirected from `/login` and `/register`
  to `/dashboard`, and the Better Auth plugin order remains unchanged.
- Session lookup failure is handled as an unauthenticated state for the landing
  page and as a fallback to showing the form for `/login` and `/register`, and it
  does not weaken dashboard protection.
