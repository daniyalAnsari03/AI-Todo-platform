import { getCookies } from "better-auth/cookies";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("postgres", () => ({ default: () => ({}) }));
vi.mock("drizzle-orm/postgres-js", () => ({ drizzle: () => ({}) }));

const ORIGINAL_BETTER_AUTH_URL = process.env.BETTER_AUTH_URL;

const SESSION_COOKIE_NAME = "session_token";

async function loadAuth() {
  vi.resetModules();
  const mod = await import("../../../auth");
  return mod.auth;
}

describe("Better Auth session cookie contract", () => {
  beforeEach(() => {
    delete process.env.BETTER_AUTH_URL;
  });

  afterEach(() => {
    if (ORIGINAL_BETTER_AUTH_URL === undefined) {
      delete process.env.BETTER_AUTH_URL;
    } else {
      process.env.BETTER_AUTH_URL = ORIGINAL_BETTER_AUTH_URL;
    }
  });

  it("names the primary session cookie exactly session_token", async () => {
    const auth = await loadAuth();
    expect(getCookies(auth.options).sessionToken.name).toBe(
      SESSION_COOKIE_NAME,
    );
  });

  it("never uses Better Auth's default prefixed cookie name", async () => {
    const auth = await loadAuth();
    expect(getCookies(auth.options).sessionToken.name).not.toBe(
      "better-auth.session_token",
    );
  });

  it("keeps the session cookie browser-compatible with the rewritten API over local http", async () => {
    const auth = await loadAuth();
    const { attributes } = getCookies(auth.options).sessionToken;
    expect(attributes.path).toBe("/");
    expect(attributes.httpOnly).toBe(true);
    expect(attributes.sameSite).toBe("lax");
    expect(attributes.secure).toBe(false);
  });

  it("marks the session cookie secure over https (production) while keeping other attributes", async () => {
    process.env.BETTER_AUTH_URL = "https://todo-app.example.vercel.app";
    const auth = await loadAuth();
    const { attributes } = getCookies(auth.options).sessionToken;
    expect(attributes.secure).toBe(true);
    expect(attributes.path).toBe("/");
    expect(attributes.httpOnly).toBe(true);
    expect(attributes.sameSite).toBe("lax");
  });
});
