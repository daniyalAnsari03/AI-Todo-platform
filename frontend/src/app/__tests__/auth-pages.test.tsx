const { redirectMock, routerPush } = vi.hoisted(() => ({
  redirectMock: vi.fn((url: string) => {
    throw new Error(`NEXT_REDIRECT:/${url.replace(/^\//, "")}`);
  }),
  routerPush: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  redirect: redirectMock,
  useRouter: () => ({ push: routerPush }),
}));

vi.mock("../../lib/auth", () => ({
  getSession: vi.fn(),
}));

import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Mock } from "vitest";

import { getSession } from "../../lib/auth";
import LoginPage from "../login/page";
import RegisterPage from "../register/page";

const mockedGetSession = getSession as Mock;

const session = {
  session: { id: "s1", expiresAt: new Date("2099-01-01") },
  user: { id: "u1", name: "alice", email: "alice@todo.local" },
};

async function captureThrown(page: () => Promise<unknown> | unknown): Promise<unknown> {
  try {
    await page();
  } catch (error) {
    return error;
  }
  return undefined;
}

describe("authenticated visitors on auth pages", () => {
  beforeEach(() => {
    redirectMock.mockClear();
    routerPush.mockClear();
    mockedGetSession.mockReset();
  });

  it("C1: /login redirects to /dashboard without rendering the form", async () => {
    mockedGetSession.mockResolvedValue(session);

    const thrown = await captureThrown(LoginPage);

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    expect(redirectMock).toHaveBeenCalledWith("/dashboard");
    expect(thrown).toBeInstanceOf(Error);
    expect((thrown as Error).message).toBe("NEXT_REDIRECT:/dashboard");
  });

  it("C2: /register redirects to /dashboard without rendering the form", async () => {
    mockedGetSession.mockResolvedValue(session);

    const thrown = await captureThrown(RegisterPage);

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    expect(redirectMock).toHaveBeenCalledWith("/dashboard");
    expect(thrown).toBeInstanceOf(Error);
    expect((thrown as Error).message).toBe("NEXT_REDIRECT:/dashboard");
  });
});

describe("unauthenticated visitors on auth pages", () => {
  beforeEach(() => {
    redirectMock.mockClear();
    routerPush.mockClear();
    mockedGetSession.mockReset();
  });

  it("C3: /login renders the login form without redirecting", async () => {
    mockedGetSession.mockResolvedValue(null);

    render(await LoginPage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(screen.getByRole("form", { name: "Log in" })).toBeInTheDocument();
  });

  it("C4: /register renders the registration form without redirecting", async () => {
    mockedGetSession.mockResolvedValue(null);

    render(await RegisterPage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(screen.getByRole("form", { name: "Register" })).toBeInTheDocument();
  });

  it("C5: /login shows the form when the session lookup fails", async () => {
    mockedGetSession.mockRejectedValue(new Error("session lookup failed"));

    render(await LoginPage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(screen.getByRole("form", { name: "Log in" })).toBeInTheDocument();
  });

  it("C6: /register shows the form when the session lookup fails", async () => {
    mockedGetSession.mockRejectedValue(new Error("session lookup failed"));

    render(await RegisterPage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    expect(redirectMock).not.toHaveBeenCalled();
    expect(screen.getByRole("form", { name: "Register" })).toBeInTheDocument();
  });
});
