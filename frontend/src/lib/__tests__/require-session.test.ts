const { redirectMock } = vi.hoisted(() => ({
  redirectMock: vi.fn(() => {
    throw new Error("NEXT_REDIRECT");
  }),
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
}));

vi.mock("../auth", () => ({
  getSession: vi.fn(),
}));

import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Mock } from "vitest";

import { getSession } from "../auth";
import { requireSession } from "../require-session";

const mockedGetSession = getSession as Mock;

describe("requireSession", () => {
  beforeEach(() => {
    redirectMock.mockClear();
    mockedGetSession.mockReset();
  });

  it("redirects unauthenticated users to /login", async () => {
    mockedGetSession.mockResolvedValue(null);

    await expect(requireSession()).rejects.toThrow("NEXT_REDIRECT");
    expect(redirectMock).toHaveBeenCalledWith("/login");
  });

  it("returns the session for an authenticated user", async () => {
    const session = {
      session: { id: "s1", expiresAt: new Date() },
      user: { id: "u1", name: "alice", email: "alice@todo.local" },
    };
    mockedGetSession.mockResolvedValue(session);

    await expect(requireSession()).resolves.toEqual(session);
    expect(redirectMock).not.toHaveBeenCalled();
  });
});