import { getCookies } from "better-auth/cookies";
import { describe, expect, it, vi } from "vitest";

vi.mock("postgres", () => ({ default: () => ({}) }));
vi.mock("drizzle-orm/postgres-js", () => ({ drizzle: () => ({}) }));

import { auth } from "../../../auth";

const SESSION_COOKIE_NAME = "session_token";

describe("Better Auth session cookie contract", () => {
  it("names the primary session cookie exactly session_token", () => {
    expect(getCookies(auth.options).sessionToken.name).toBe(SESSION_COOKIE_NAME);
  });

  it("never uses Better Auth's default prefixed cookie name", () => {
    expect(getCookies(auth.options).sessionToken.name).not.toBe(
      "better-auth.session_token",
    );
  });

  it("keeps the session cookie browser-compatible with the rewritten API", () => {
    const { attributes } = getCookies(auth.options).sessionToken;
    expect(attributes.path).toBe("/");
    expect(attributes.httpOnly).toBe(true);
    expect(attributes.sameSite).toBe("lax");
    expect(attributes.secure).toBe(false);
  });
});
