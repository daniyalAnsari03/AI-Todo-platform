# Contract — JWT Bearer verification (backend ↔ Better Auth JWT plugin)

Date: 2026-10-24. Implementation contract for FR-220–229, NFR-001–003, informed by
the installed better-auth 1.7.5 source (details + evidence in `research.md`).
The OQ-8 decision is **DECIDED — approved by user: Option A** (asymmetric
RS256 signing via the plugin's native JWKS; the backend verifies with the
public key). Option B is retained below only as a historical record of the
alternative that was not chosen.

## Token issuance (frontend, Better Auth JWT plugin)

- `frontend/auth.ts` registers the plugin (`better-auth/plugins/jwt`) with:
  - `jwt.expirationTime: "7d"` (FR-226; plugin default is 15m — must override).
  - `jwt.issuer` / `jwt.audience` pinned to the `BETTER_AUTH_URL` origin
    (backend must set the identical values for exact-match validation).
  - OQ-8-dependent signing configuration (see below).
- Claims (per installed source `sign.mjs`):
  - `sub` = Better Auth `user.id` (the value used as `{user_id}` in API paths).
  - `exp` = issue time + 7d; `iat` set automatically.
  - `iss` = configured issuer; `aud` = configured audience.
  - Payload base = the session's user record (plugin default `definePayload`
    behavior); extra claims are permitted but only `sub`/`exp`/`iss`/`aud` are
    contractual.
- Issuance points: `GET /api/auth/token` (Better Auth route, response
  `{"token": "..."}`) after login, and `set-auth-jwt` response header on
  `/get-session`.

## Frontend usage (FR-221, FR-233)

- Client obtains the token once per login/reload via `GET /api/auth/token` with the
  Better Auth session cookie; stored in memory only (`src/lib/token.ts`).
- **Every** task API call sends `Authorization: Bearer <token>`; on 401 the client
  invalidates the token, retries token acquisition once, and on failure routes to
  `/login`.

## Backend verification (`src/todo_app/auth.py:get_current_user`)

Order of operations (401 on any failure before authorizing):

1. Startup fail-fast (per Amendment 1 of `spec.md`): the JWT/JWKS verification
   configuration must be present — JWKS URL (default `BETTER_AUTH_URL` +
   `/api/auth/jwks`, env-overridable), issuer, audience — otherwise the app
   refuses to start with a clear error (never printing any secret value).
   `BETTER_AUTH_SECRET` is **frontend-only** (Better Auth); the backend no
   longer requires or reads it.
2. Header must be exactly `Authorization: Bearer <single JWT>` (case-insensitive
   scheme; extra whitespace tolerated). Missing/malformed → 401.
3. Signature verification — algorithm allowlist ONLY (no `alg: none`), `exp`
   checked (leeway 60s; OQ-7 DECIDED — approved by user), `iss` and `aud`
   exact match; unknown `kid` → refresh JWKS once, else 401.
4. `sub` extracted; `User` row loaded from DB (token user must exist);
   missing user → 401.
5. Result returned as the dependency value; route-level code enforces the
   `{user_id}`-path matches-token rule (403) *before any DB query by the route*.

### Option A — JWKS verification (OQ-8 DECIDED — approved by user)

- Plugin config: `jwks: { keyPairConfig: { alg: "RS256" } }` (RS256 preferred for
  Python-side verification; EdDSA/ES256/PS256 also viable with the same code).
- Backend dependency: `pyjwt[crypto]` (implies `cryptography`). Uses
  `jwt.PyJWKClient` pointing at `JWT_JWKS_URL` (default
  `BETTER_AUTH_URL` + `/api/auth/jwks`, env-overridable).
- **JWKS caching & failure behavior (contract):**
  - Keys are cached **in memory** after the first successful `GET {JWKS_URL}`;
    the cache is keyed by `kid`.
  - On an unknown `kid` (Better Auth key rotation — `jwks.rotationInterval`, if
    ever enabled), the client refreshes the JWKS document **once** per request
    and retries verification; a still-unknown `kid` after refresh → **401**.
  - JWKS endpoint **unreachable on first use** (no cache yet) → **HTTP 503**
    (`{"detail": "..."}`): the token could not be verified through no client
    fault; the request is safe to retry. Unreachable during a
    refresh-on-unknown-`kid` (stale cache exists) → **503** as well — never a
    fallback to stale-key acceptance or 404.
  - Verification never silently downgrades (no `alg`/`kid` fallbacks; the
    algorithm allowlist is always enforced against the JWKS-resolved key).
  - A small TTL may refresh the cache proactively; correctness never depends
    on TTL alone (unknown-`kid` refresh is the authoritative trigger).
- Consequences: the `jwks` DB table must exist (Better Auth lazily mints keys) —
  DB schema change that **remains an approval-gated task** (backup + explicit
  user approval before any DB schema change executes; see `data-model.md` §4);
  backend verification depends on the frontend's JWKS endpoint being reachable
  (first-verification-only, thanks to caching; unreachable → 503 per above).

### Option B — shared-secret HS256 via the plugin's custom sign callback (NOT chosen)

- Plugin config: `jwt: { sign: <custom HS256 callback signing with
  BETTER_AUTH_SECRET> }` + the required (placeholding) `jwks.remoteUrl` option
  (plugin throws without it — `index.mjs:24`).
- Backend dependency: same `pyjwt[crypto]`; verifies HS256 directly against
  `BETTER_AUTH_SECRET` (binding the PDF's literal "shared secret" wording).
- Consequences: no `jwks` table/DB change; but a non-primary, escape-hatch-style
  configuration; key rotation unsupported by the plugin itself.

## What is retired (FR-228, OQ-3 recommendation)

- FastAPI cookie/session verification path AND `session_token_from_cookie` +
  `SESSION_COOKIE_NAME` removed in the same release; `tests/test_auth.py`
  rewritten accordingly (9 tests → JWT suite). No dual-accept window.
- Better Auth session cookies themselves KEEP working for the frontend's own
  Better Auth routes (login/logout/`/token`); `nextCookies()` in
  `frontend/auth.ts` stays — the backend just stops consuming them.
- `allow_credentials=True` on backend CORS dropped (NFR-006 note).

## Error contract

- 401 body: `{"detail": "Not authenticated" | "Invalid token" | "Token expired" |
  "User not found"}` (wording implementation detail); never leaks why in
  machine-critical ways beyond that; no secrets echoed.
- 403 body: `{"detail": "..."}`; no task data, no indication whether the path
  user exists.
