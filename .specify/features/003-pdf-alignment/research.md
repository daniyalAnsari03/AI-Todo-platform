# Research — 003-pdf-alignment (PLAN stage)

Date: 2026-10-24. Scope: evidence gathering for the plan. No source code, deps, DB, env
touched.

> **Decision record (plan-correction pass, 2026-10-24): OQ-8 = Option A — DECIDED —
> approved by user.** Asymmetric RS256 signing via the plugin's native JWKS; the
> backend verifies with the public key (PyJWKClient). The evidence below stands as
> the basis for that decision.

## OQ-8 — Better Auth JWT plugin: signing algorithm / key mechanism (RESEARCHED, from installed source)

Installed version evidence: `frontend/node_modules/better-auth/package.json` →
`"version": "1.7.5"` (package.json in repo declares `^1.3.0`; the lockfile resolved to
1.7.5).

### Finding 1 — the JWT plugin is asymmetric-only. Shared-secret HS256 is NOT supported.

- `frontend/node_modules/better-auth/dist/plugins/jwt/sign.mjs:67`:
  `const alg = key.alg ?? options?.jwks?.keyPairConfig?.alg ?? "EdDSA";`
- `frontend/node_modules/better-auth/dist/plugins/jwt/types.d.mts:217-232` (type
  definition of `JWKOptions`): `"Asymmetric (JWS) Supported."` — the union is
  `"EdDSA" | "ES256" | "ES512" | "PS256" | "RS256"`. **No HS256/OCT key type exists.**
  The only HS256 references in the entire dist tree are for *email-verification*
  tokens (`dist/api/routes/email-verification.mjs`), not the JWT plugin.
- Keys are managed in a DB table named `jwks` (plugin schema,
  `dist/plugins/jwt/schema.mjs:2`: `const schema = { jwks: { fields: { publicKey… privateKey… createdAt… } } }`),
  auto-minted lazily by `createJwk` (`dist/plugins/jwt/utils.mjs:43`) and published at
  `GET /jwks` (`dist/plugins/jwt/index.mjs:45`).
- A repo-wide grep confirms HS256 exists only in `dist/crypto/jwt.mjs` and
  `dist/api/routes/email-verification.mjs` — neither is the JWT plugin's signing path.

### Finding 2 — token issuance and retrieval

- Token endpoint: `dist/plugins/jwt/index.mjs:141`:
  `getToken: createAuthEndpoint("/token", { method: "GET", requireHeaders: true, use: [sessionMiddleware] … })`
  → returns `{ token }`, **requires an authenticated Better Auth session** (the session
  cookie must reach the frontend's `/api/auth/*` handler).
- Alternative: a `/get-session` after-hook sets the header
  (`index.mjs:205`: `ctx.setHeader("set-auth-jwt", jwt);`).

### Finding 3 — token contents

- `sub` = Better Auth user id (`sign.mjs:125`: `sub: … ?? ctx.context.session.user.id`).
- `iss`/`aud` default to the configured `baseURL` origin
  (`sign.mjs:86`: `const defaultIss = options?.jwt?.issuer ?? baseURLOrigin;`).
- `exp` defaults to **15m** (`sign.mjs:81`:
  `const defaultExp = toExpJWT(options?.jwt?.expirationTime ?? "15m", iat ?? nowSeconds);`)
  → must set `jwt({ jwt: { expirationTime: "7d" } })` for FR-226's 7-day default.
- Protected header always carries `alg` and `kid` (`sign.mjs:107-111`).

### Finding 4 — supported/config options (from `types.d.mts`, plugin 1.7.5)

- `jwt.issuer`, `jwt.audience`, `jwt.expirationTime`, `jwt.definePayload`,
  `jwt.getSubject`, `jwt.sign` (custom signing callback; requires `jwks.remoteUrl`
  — `index.mjs:24`:
  `if (options?.jwt?.sign && !options.jwks?.remoteUrl) throw new BetterAuthError("options.jwks.remoteUrl must be set when using options.jwt.sign");`),
  `jwks.keyPairConfig.alg` (one of the asymmetric union above).
- There is no `HS256` / symmetric option anywhere in the plugin's option surface.

### Consequence for FR-222 ("shared-secret verification")

The PDF's literal mechanism (FastAPI verifies HS256 with `BETTER_AUTH_SECRET`) **cannot
work with the JWT plugin as installed**: it only signs with asymmetric keys, and those
keys live in a `jwks` DB table (adding that table = DB schema change requiring explicit
user approval). Realistic options are evaluated in `plan.md` §OQ-8:

- **Option A (recommended)**: JWT plugin with `keyPairConfig.alg = "RS256"`
  (most portable into the Python ecosystem), `expirationTime: "7d"`, issuer/audience
  pinned; FastAPI verifies via the plugin's published `GET /jwks` (PyJWT
  `PyJWKClient`). Requires: new `jwks` table (approval), new backend dep
  `pyjwt[crypto]` (approval at implement stage). **CHOSEN** (OQ-8 decided =
  Option A).
- **Option B**: plugin escape hatch `jwt.sign` custom callback that signs HS256 with
  `BETTER_AUTH_SECRET`; no `jwks` table. Non-primary path; keeps the PDF's literal
  wording; slightly fragile (requires a placeholder `remoteUrl`). **Not chosen.**
- **Option C (rejected)**: backend reads/decrypts `jwk.private_key` rows from the
  shared DB — re-implements Better Auth's secret-encryption scheme and defeats key
  rotation. (Rejected.)

## Other research notes

- **Backend test inventory**: 54 tests confirmed — `tests/test_api.py` 15
  (class-based, `httpx.AsyncClient` + in-memory SQLite), `tests/test_auth.py` 9,
  `tests/test_cli.py` 6, `tests/test_models.py` 5, `tests/test_store.py` 19.
- **Frontend test inventory**: 26 tests confirmed — `logout/route.test.ts` 1,
  `AuthForm.test.tsx` 6, `TodoList.test.tsx` 7, `auth-cookies.test.ts` 3,
  `auth-handler.test.ts` 7, `require-session.test.ts` 2.
- **Current auth flow (to retire)**: cookie `session_token` → `session` row lookup in
  `src/todo_app/auth.py:32`; frontend proxies `/api/items` through a Next.js rewrite
  with same-origin cookie (`frontend/next.config.js`,
  `frontend/src/lib/api.ts:16`).
- **`BETTER_AUTH_URL`/base URL**: `frontend/auth.ts:17` defaults to
  `http://localhost:3000`; the backend can reuse the same env var for the JWKS URL
  (`BETTER_AUTH_URL` + `/api/auth/jwks`).
- **Better Auth sessions remain**: the JWT plugin supplements (does not replace)
  Better Auth's session/login; `GET /token` needs a live session. So user/session/
  account tables stay, and register/login/logout pages keep working as-is; only the
  *backend's* cookie-verification dependency is retired (FR-228 scope of decision in
  OQ-3).
- **Next.js 16 upgrade (OQ-4)**: no Next 16 package/docs are installed in the repo,
  so claims about 16.x specifics cannot be verified offline here; conclusions in the
  plan (isolated step, verify tests/build, rollback via commit-restored
  `package-lock.json`) treat the upgrade as an implement-stage operation with
  verification, not an assumption.
- **SQLModel migrations**: backend has no Alembic; `init_db()` uses
  `create_all` (creates missing tables only). Taking on Alembic for one structural
  change is disproportionate; the plan proposes a small audited migration script +
  backup instead (see `data-model.md`).
