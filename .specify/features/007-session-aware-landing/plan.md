# Implementation Plan: Session-Aware Landing Page

**Branch**: `007-session-aware-landing` | **Date**: 2026-11-04
**Spec**: `.specify/features/007-session-aware-landing/spec.md`
**Status**: Approved (2026-11-04)

## Summary

Make the public landing page at `/` session-aware using the existing server-side
`getSession` lookup. Authenticated visitors see a Dashboard navigation entry and a
"Go to Dashboard" hero CTA; unauthenticated visitors keep the current Login, Get
Started, and `/register` CTA experience. Authenticated visitors who open `/login`
or `/register` are redirected to `/dashboard` by a page-level check using the same
`getSession`. The existing session guard, session cookie, token/JWT handling,
logout flow, Better Auth configuration, backend, and database remain unchanged.

## Technical Context

**Frontend**: TypeScript, React 19, Next.js 16.4.3, App Router.
**Session source**: Existing `getSession` in `frontend/src/lib/auth.ts`; it reads
request headers and calls `auth.api.getSession` read-only.
**Redirects**: Existing `next/navigation` `redirect` used at page level.
**Navigation**: `LandingNavigation` is already a client component shared by the
desktop and mobile menus.
**Tests**: Vitest 3.2.7 and Testing Library; baseline confirmed at **70 tests in
16 files** by running `npm test` on 2026-11-04.
**Backend / Phase I**: Python/FastAPI and CLI, untouched; regression check only.
**Constraints**: No new dependencies, routes, auth mechanisms, client-persisted
auth state, database changes, environment changes, or git operations. Do not read
or print environment values.

## Constitution Check

- **Spec-First**: Pass - the approved spec is the sole source of the behavior in
  this plan.
- **Test-First**: Required - the new focused tests are written and shown RED
  before production edits; implementation starts only after task approval.
- **Lifecycle & Review Gates**: Pass - this document is the Plan stage only;
  Tasks and Implement remain blocked until their gates are approved.
- **Runtime, dependencies, and layout**: Pass - no dependency, runtime, package
  layout, backend, or database change.
- **Scope discipline**: Pass - only the four production files named in the spec
  are touched; protected auth and backend files are explicitly excluded.
- **Security**: Pass - no secrets, environment files, database access, or client
  auth persistence is introduced.

## Design and Execution

### 1. Landing page reads the session server-side

`frontend/src/app/page.tsx` becomes an `async` Server Component:

```tsx
export default async function HomePage() {
  let isAuthenticated = false;
  try {
    isAuthenticated = (await getSession()) !== null;
  } catch {
    isAuthenticated = false;
  }

  return (
    <main className="landing-shell">
      <LandingNavigation isAuthenticated={isAuthenticated} />
      {/* existing landing content */}
    </main>
  );
}
```

- `getSession` is imported from `../lib/auth`; no session logic is duplicated.
- Only the `getSession` call is inside `try/catch`. No `redirect` is called on `/`,
  so there is no redirect path from the landing page.
- The catch is the required FR-016/edge-case fallback for the landing page: a
  missing, malformed, expired, or unreadable session, or a lookup error, produces
  the unauthenticated presentation. Diagnostic detail, if added later, stays in
  server-side logging only; no error is shown to the visitor.
- No client component stores authentication state. The value is computed per
  request and passed as a prop.

### 2. Landing navigation receives `isAuthenticated`

`frontend/src/components/LandingNavigation.tsx`:

- Add a required prop `isAuthenticated: boolean` to `LandingNavigation`.
- Pass it to the shared `NavigationLinks` component used by **both** the desktop
  `<nav aria-label="Main navigation">` and the mobile
  `<nav aria-label="Mobile main navigation">`. One conditional therefore covers
  FR-002 and FR-003 consistently.
- Keep Home, Features, and About unchanged.
- Authenticated branch: render exactly one link labeled `Dashboard` targeting
  `/dashboard`. Do not render Login or Get Started.
- Unauthenticated branch: render Login targeting `/login` and Get Started
  targeting `/register`, preserving the existing `nav-cta` class on Get Started.
- Reuse the `nav-cta` class on the Dashboard link so the existing visual system is
  preserved (styling is not otherwise specified by the spec).

```tsx
function NavigationLinks({ isAuthenticated, onNavigate }) {
  return (
    <>
      {/* Home, Features, About unchanged */}
      {isAuthenticated ? (
        <Link href="/dashboard" className="nav-cta" onClick={onNavigate}>
          Dashboard
        </Link>
      ) : (
        <>
          <Link href="/login" onClick={onNavigate}>Login</Link>
          <Link href="/register" className="nav-cta" onClick={onNavigate}>
            Get Started
          </Link>
        </>
      )}
    </>
  );
}
```

### 3. Hero CTA switches by session state

In `frontend/src/app/page.tsx`, only the primary hero CTA changes:

```tsx
{isAuthenticated ? (
  <Link href="/dashboard" className="button-primary large">
    Go to Dashboard
  </Link>
) : (
  <Link href="/register" className="button-primary large">
    Get Started Free
  </Link>
)}
```

The secondary "Learn More" CTA, hero copy, stats, preview, features, about
section, footer (including the existing footer Dashboard link), and all CSS remain
unchanged. This preserves FR-011.

### 4. `/login` and `/register` page-level redirects

`frontend/src/app/login/page.tsx` and `frontend/src/app/register/page.tsx` become
`async` Server Components:

```tsx
export default async function LoginPage() {
  let isAuthenticated = false;
  try {
    isAuthenticated = (await getSession()) !== null;
  } catch {
    isAuthenticated = false;
  }

  if (isAuthenticated) {
    redirect("/dashboard");
  }

  return (
    <main className="auth-page">
      <AuthForm mode="login" />
    </main>
  );
}
```

- `redirect` is deliberately **outside** the `try/catch`. Next.js implements
  `redirect()` by throwing `NEXT_REDIRECT`; placing it inside the catch would
  swallow the redirect and show the form to an authenticated visitor.
- `getSession` is imported read-only from `../../lib/auth`. No Better Auth,
  cookie, token, `auth-handler`, or `requireSession` change is made.
- `AuthForm` and its client behavior are untouched.
- The register page follows the same shape with `mode="register"`.
- No `export const dynamic`, proxy, middleware, or new route is introduced.

### 5. Rendering and caching evidence (Next.js 16.4.3)

The landing and auth pages must not be statically cached with a stale session
state. The planned implementation relies on the installed Next.js behavior, not on
a guess:

- Installed version: `frontend/node_modules/next/package.json` reports
  **16.4.3**.
- `frontend/src/lib/auth.ts:13` calls `await headers()` inside `getSession`.
- Installed docs,
  `frontend/node_modules/next/dist/docs/01-app/03-api-reference/04-functions/headers.md:48`:
  "`headers` is a Request-time API whose returned values cannot be known ahead of
  time. Using it in will opt a route into **dynamic rendering**."
- Installed glossary,
  `frontend/node_modules/next/dist/docs/01-app/04-glossary.md:195-202`, lists
  `headers()` as a Request-time API that causes a component to opt into dynamic
  rendering.
- `frontend/next.config.js` does not enable `cacheComponents`, and no route
  segment sets `dynamic = "force-static"` or `revalidate`. The default Next.js 16
  behavior described by the installed docs therefore applies.
- Consequently `/`, `/login`, and `/register` are rendered at request time because
  each awaits `getSession`, which reads `headers()`. No `force-dynamic` directive
  is required, and none is planned.
- The production build verification will confirm these routes are server-rendered
  on demand (dynamic) rather than prerendered static output.

### 6. Failure handling and redirect-loop avoidance

- **Landing lookup failure**: catch and treat as unauthenticated. `/` never
  redirects and always renders.
- **Auth-page lookup failure**: catch and treat as unauthenticated, so the form is
  shown. No redirect and no crash.
- **Missing/invalid/expired session**: `getSession` returns `null`; treated as
  unauthenticated.
- **No redirect loop**:
  - `/` never redirects.
  - `/login` and `/register` redirect only when `getSession` returns a session.
  - `/dashboard` continues to use `requireSession`, which redirects to `/login`
    only when `getSession` returns `null`.
  - If a session expires between the auth-page check and the dashboard render, the
    dashboard sends the visitor to `/login` once; the login page then sees no
    session and renders the form. There is no cycle.
- **Failure does not weaken dashboard protection**: `requireSession` remains the
  only dashboard guard and is not modified.

## Planned Files

### Production files to modify

```text
frontend/src/app/page.tsx                       # async session read; hero CTA switch
frontend/src/components/LandingNavigation.tsx   # isAuthenticated prop; shared nav links
frontend/src/app/login/page.tsx                 # authenticated -> /dashboard redirect
frontend/src/app/register/page.tsx              # authenticated -> /dashboard redirect
```

### Test files to add

```text
frontend/src/app/__tests__/landing-page.test.tsx
frontend/src/app/__tests__/auth-pages.test.tsx
frontend/src/components/__tests__/LandingNavigation.session.test.tsx
```

### Existing test files to update (setup only; assertions preserved)

```text
frontend/src/components/__tests__/ResponsiveNavigation.test.tsx
frontend/src/components/__tests__/AuthForm.test.tsx
```

### Files and areas that MUST NOT change

```text
frontend/src/lib/require-session.ts
frontend/src/lib/auth.ts
frontend/src/lib/auth-handler.ts
frontend/src/lib/token.ts
frontend/auth.ts
frontend/src/app/logout/route.ts
frontend/src/app/api/auth/[...all]/route.ts
frontend/next.config.js
frontend/package.json
frontend/src/app/globals.css
frontend/src/app/dashboard/page.tsx
frontend/src/components/AuthForm.tsx
frontend/src/components/DashboardSidebar.tsx
src/todo_app/**                    # backend and Phase I CLI
tests/**                           # backend/Phase I tests
database schema, migrations, environment files, secrets, git state
```

## Test Strategy (Test-First)

All page tests mock the existing session module instead of `next/headers`, so no
real request context, database, or auth backend is used:

```ts
vi.mock("../../lib/auth", () => ({ getSession: vi.fn() }));
```

Component tests do not need `getSession`: `LandingNavigation` receives
`isAuthenticated` as a prop. The existing `server-only` alias in
`frontend/vitest.config.ts` remains unchanged.

### New tests

| ID | Test | File | Mock setup | Expected RED reason before implementation |
|----|------|------|------------|-------------------------------------------|
| A1 | Authenticated `/` shows Dashboard in desktop nav, hides Login/Get Started, and shows a "Go to Dashboard" hero CTA targeting `/dashboard`. | `frontend/src/app/__tests__/landing-page.test.tsx` | `getSession` resolves a minimal valid session; render `await HomePage()`. | Page is not session-aware and ignores `getSession`; it renders Login/Get Started and "Get Started Free" to `/register`, so Dashboard and "Go to Dashboard" assertions fail. |
| A2 | Unauthenticated `/` renders publicly with Login `/login`, Get Started `/register`, and "Get Started Free" `/register`, and performs the lookup. | same | `getSession` resolves `null`. | Visible output already matches, but the test asserts `getSession` was called once; the pre-implementation page never calls it, so the test is RED. |
| A3 | Landing lookup failure falls back to unauthenticated presentation without throwing or redirecting. | same | `getSession` rejects with an error. | The test asserts `getSession` was called and the fallback path exists; the pre-implementation page never calls `getSession`, so it is RED. |
| A4 | A later load after session end shows the unauthenticated state. | same | `getSession` resolves a session on the first call and `null` on the second. | First render lacks Dashboard before implementation, so the authenticated assertion fails (RED); this covers FR-008/AC-005 on next load. |
| B1 | Desktop navigation switches between unauthenticated (Login/Get Started) and authenticated (Dashboard `/dashboard`, no Login/Get Started), preserving Home/Features/About. | `frontend/src/components/__tests__/LandingNavigation.session.test.tsx` | Render with `isAuthenticated={false}`, then rerender with `true`; no session mock. | The prop does not exist/is ignored before implementation, so the authenticated rerender still shows Login/Get Started and no Dashboard (RED). |
| B2 | Mobile navigation switches the same way inside the opened mobile menu. | same | Render `isAuthenticated={false}`, open the mobile menu, assert; rerender `true`, assert. | Same as B1: the prop is ignored, so the mobile authenticated assertions fail (RED). |
| C1 | Authenticated `/login` redirects to `/dashboard` and does not render the form. | `frontend/src/app/__tests__/auth-pages.test.tsx` | `getSession` resolves a session; `next/navigation.redirect` mocked to throw `NEXT_REDIRECT:/dashboard`. | The page does not call `getSession` or redirect before implementation, so the expected rejection/redirect assertion fails (RED). |
| C2 | Authenticated `/register` redirects to `/dashboard` and does not render the form. | same | Same as C1. | Same as C1 (RED). |
| C3 | Unauthenticated `/login` renders the login form, does not redirect, and performs the lookup. | same | `getSession` resolves `null`; `redirect` mock does not throw. | Form output already matches, but the test asserts `getSession` was called once; the pre-implementation page never calls it (RED). |
| C4 | Unauthenticated `/register` renders the registration form, does not redirect, and performs the lookup. | same | Same as C3. | Same as C3 (RED). |
| C5 | `/login` lookup failure shows the form without redirecting or crashing. | same | `getSession` rejects; `redirect` mock does not throw. | The test asserts the lookup occurred; the pre-implementation page never calls `getSession` (RED). |
| C6 | `/register` lookup failure shows the form without redirecting or crashing. | same | Same as C5. | Same as C5 (RED). |

Planned new-test count: **12**. Expected full frontend suite after implementation:
**82 tests** (70 baseline + 12 new).

### Existing tests: changes and obsolete assertions

- `frontend/src/components/__tests__/ResponsiveNavigation.test.tsx`: change
  `render(<LandingNavigation />)` to
  `render(<LandingNavigation isAuthenticated={false} />)`. The existing mobile
  Features/Get Started assertions remain valid. This is a required fixture update
  because the new prop is required; no assertion becomes obsolete.
- `frontend/src/components/__tests__/AuthForm.test.tsx` (`HomePage` block): add a
  `getSession` mock resolving `null` and keep the existing public-landing
  assertions. The page now reads request-scoped session data, which is not
  available in jsdom; explicit mocking keeps the test deterministic. This is a
  setup update; the unauthenticated assertions remain valid.
- **No existing assertion is made obsolete by the approved spec.** The only
  landing-page assertion set is the unauthenticated state, which the spec requires
  to remain unchanged.

## Traceability

### Functional Requirements

| Requirement | Plan section | Planned verification |
|-------------|--------------|----------------------|
| FR-001 | §1, §5 | A1-A4 |
| FR-002 | §2 | A1, B1 |
| FR-003 | §2 | A1, B2 |
| FR-004 | §3 | A1, B1, B2 |
| FR-005 | §2, §3 | A2, B1, B2, updated `AuthForm.test.tsx` HomePage test |
| FR-006 | §1, §6 | A2, A3; `/` has no redirect call |
| FR-007 | §6; unchanged `requireSession` | Existing `require-session.test.ts`; AC-003 manual check |
| FR-008 | §1, §6 | A2, A4; no client auth storage |
| FR-009 | §4, Planned Files | Protected-file diff check; C1-C6; existing auth tests |
| FR-010 | §4, Planned Files | C1-C6; no new routes/dependencies |
| FR-011 | §2, §3 | A2, B1, B2; unchanged CSS/footer/copy |
| FR-012 | Test Strategy | A1-A4, B1-B2, C1-C6 |
| FR-013 | Verification | Full frontend suite, production build, backend/Phase I suite |
| FR-014 | §4 | C1, C2 |
| FR-015 | §4 | C3, C4 |
| FR-016 | §6 | A3, C5, C6 |

### Acceptance Criteria

| Criterion | Plan section | Planned verification |
|-----------|--------------|----------------------|
| AC-001 | §2 | A1, B1, B2 |
| AC-002 | §3 | A1 |
| AC-003 | §6; unchanged guard | Existing `require-session.test.ts`; manual checklist |
| AC-004 | §1, §3 | A2; updated `AuthForm.test.tsx` HomePage test |
| AC-005 | §1, §6 | A4 |
| AC-006 | §6 | A3 |
| AC-007 | §6; unchanged guard | Existing `require-session.test.ts` (null -> `/login`) |
| AC-008 | Test Strategy | 70 baseline tests plus 12 new tests |
| AC-009 | Verification | `npm run build` |
| AC-010 | Planned Files | Diff review plus backend/Phase I regression suite |
| AC-011 | §4 | C1 |
| AC-012 | §4 | C2 |
| AC-013 | §4, §6 | C3-C6 |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| `redirect()` throws `NEXT_REDIRECT` and could be swallowed by `try/catch`. | Keep only `getSession` inside `try/catch`; call `redirect` after it. C1/C2 assert the redirect rejection. |
| A session lookup failure crashes `/` or shows an error. | Catch and fall back to unauthenticated; A3 asserts no throw and unauth output. |
| A lookup failure crashes `/login` or `/register`. | Catch and render the form; C5/C6 assert form output and no redirect. |
| Redirect loop between `/login` and `/dashboard`. | `/login` redirects only on a non-null session; `requireSession` redirects only on null; expiry yields one hop back to the form. Covered by C1-C4 and existing `require-session.test.ts`. |
| Static caching freezes a stale authenticated/unauth state. | `getSession` reads `headers()`, which the installed Next 16 docs mark as opting the route into dynamic rendering; no static override exists. Confirm in build output. |
| Accidentally changing protected auth/backend behavior. | Explicit must-not-change list; reuse `getSession` read-only; no changes to `requireSession`, `auth.ts`, `auth-handler.ts`, `token.ts`, logout, backend, or schema; diff review before reporting. |
| Client-side auth state outlives the session. | No localStorage, cookies, or context is added; the boolean is a per-request server prop. A4 verifies the next load reverts. |
| Existing tests break from the new required prop or async page. | Update only the two fixtures described above; keep all assertions; full 70-test baseline must remain green. |
| Visual regression from conditional links. | Keep existing classes, markup structure, copy, CSS, and footer unchanged except the specified link/CTA branches. |
| Tests depend on real request headers or a database. | Page tests mock `lib/auth`; component tests use props; no real DB/auth calls. |
| Backend or Phase I regression. | Run the full backend unittest suite unchanged and compare with the recorded baseline. |

## Assumptions and Ambiguities

1. The spec header still says "Draft v2 - awaiting final spec approval", while the
   stage instruction states the spec is approved. This plan treats the spec as
   approved per the instruction and records the discrepancy rather than editing
   the spec.
2. "Dashboard in place of Login and Get Started" is interpreted as keeping Home,
   Features, and About, removing Login and Get Started, and adding one Dashboard
   link in both menus.
3. The spec does not prescribe styling for the Dashboard navigation link. The plan
   reuses the existing `nav-cta` class to preserve the current visual system.
4. The spec permits diagnostic detail in server-side logging but does not require
   logging. The plan performs a silent fallback; no client-visible detail is added.
5. The redirect status code is not specified; the plan uses the existing Next.js
   `redirect("/dashboard")` default.
6. The 70-test baseline was confirmed locally (16 files, 70 tests). The planned
   total after implementation is 82 tests.

## Verification Sequence

From the repository root in PowerShell:

```powershell
# 1. RED: run only the new focused tests before implementation and record failures.
Set-Location frontend
npm test -- src/app/__tests__/landing-page.test.tsx src/app/__tests__/auth-pages.test.tsx src/components/__tests__/LandingNavigation.session.test.tsx

# 2. GREEN: full frontend suite; expected 82 tests (70 baseline + 12 new).
npm test

# 3. Production build; confirm /, /login, /register are dynamic/request-rendered.
npm run build

# 4. Backend and Phase I suites, unchanged; compare with the recorded baseline.
Set-Location ..
uv run python -m unittest discover -s tests
```

Then complete the spec's Manual Verification Checklist:

- [ ] Log in, open `/`, confirm Dashboard and "Go to Dashboard" at desktop and
  mobile width with no Login/Get Started.
- [ ] Activate Dashboard and confirm the dashboard opens without a login prompt.
- [ ] While logged in, visit `/login` and `/register` and confirm both redirect to
  `/dashboard`.
- [ ] Close/reopen the tab, visit `/`, and confirm the authenticated state remains.
- [ ] Log out, visit `/`, confirm Login/Get Started and "Get Started Free" return,
  and confirm `/dashboard` redirects to `/login`.

## Complexity Tracking

No new dependency, route, persistence layer, or authentication mechanism is
planned. The only new logic is a per-request boolean derived from the existing
`getSession`, a conditional navigation/CTA branch, and a page-level redirect that
reuses the existing `getSession`. The backend, database, Phase I CLI, auth guard,
token handling, logout flow, and Better Auth configuration remain untouched.
