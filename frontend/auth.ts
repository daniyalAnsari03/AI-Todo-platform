// Task T-039 · Spec FR-220, FR-226, FR-229 + Amendment 1 · Plan §Auth plan (frontend) · Contract auth-jwt.md §Token issuance
import "server-only";

import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { nextCookies } from "better-auth/next-js";
import { jwt } from "better-auth/plugins/jwt";
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";

import * as schema from "./src/lib/schema";

const connectionUrl = process.env.DATABASE_URL ?? "";
const client = postgres(connectionUrl, { max: 1, prepare: false });
const db = drizzle(client, { schema });

// Issuer/audience pinned to the BETTER_AUTH_URL origin (read from process
// env at runtime, reusing the existing baseURL fallback), never a new
// hard-coded JWT constant. The backend must verify against this exact
// origin (contract auth-jwt.md: JWT_ISSUER / JWT_AUDIENCE).
const baseURL = process.env.BETTER_AUTH_URL ?? "http://localhost:3000";
const authOrigin = new URL(baseURL).origin;

export const auth = betterAuth({
  secret: process.env.BETTER_AUTH_SECRET,
  baseURL,
  database: drizzleAdapter(db, {
    provider: "pg",
    schema: {
      user: schema.user,
      session: schema.session,
      account: schema.account,
      verification: schema.verification,
      jwks: schema.jwks,
    },
  }),
  emailAndPassword: {
    enabled: true,
  },
  advanced: {
    cookiePrefix: "",
    useSecureCookies: false,
    cookies: {
      // Must match the cookie the FastAPI backend reads in
      // src/todo_app/auth.py. cookiePrefix alone cannot express this: Better
      // Auth treats it as a truthy-or-default string, so "" falls back to
      // "better-auth" and the cookie would be "better-auth.session_token".
      session_token: { name: "session_token" },
    },
  },
  plugins: [
    nextCookies(),
    jwt({
      jwt: {
        issuer: authOrigin,
        audience: authOrigin,
        expirationTime: "7d",
      },
      jwks: {
        keyPairConfig: {
          alg: "RS256",
        },
      },
    }),
  ],
});