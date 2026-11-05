import { cleanup, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Mock } from "vitest";

vi.mock("../../lib/auth", () => ({
  getSession: vi.fn(),
}));

import { getSession } from "../../lib/auth";
import HomePage from "../page";

const mockedGetSession = getSession as Mock;

const session = {
  session: { id: "s1", expiresAt: new Date("2099-01-01") },
  user: { id: "u1", name: "alice", email: "alice@todo.local" },
};

function desktopNavigation() {
  return within(screen.getByRole("navigation", { name: "Main navigation" }));
}

describe("session-aware landing page", () => {
  beforeEach(() => {
    mockedGetSession.mockReset();
  });

  it("A1: authenticated visitors see Dashboard navigation and a Go to Dashboard hero CTA", async () => {
    mockedGetSession.mockResolvedValue(session);

    render(await HomePage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    const desktop = desktopNavigation();
    expect(desktop.getByRole("link", { name: "Dashboard" })).toHaveAttribute(
      "href",
      "/dashboard",
    );
    expect(desktop.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
    expect(desktop.queryByRole("link", { name: "Get Started" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Go to Dashboard" })).toHaveAttribute(
      "href",
      "/dashboard",
    );
    expect(screen.queryByRole("link", { name: /get started free/i })).not.toBeInTheDocument();
  });

  it("A2: unauthenticated visitors keep the public landing navigation and CTA", async () => {
    mockedGetSession.mockResolvedValue(null);

    render(await HomePage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    const desktop = desktopNavigation();
    expect(desktop.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(desktop.getByRole("link", { name: "Get Started" })).toHaveAttribute(
      "href",
      "/register",
    );
    expect(desktop.queryByRole("link", { name: "Dashboard" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /get started free/i })).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("A3: a lookup failure falls back to the unauthenticated presentation", async () => {
    mockedGetSession.mockRejectedValue(new Error("session lookup failed"));

    render(await HomePage());

    expect(mockedGetSession).toHaveBeenCalledTimes(1);
    const desktop = desktopNavigation();
    expect(desktop.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(desktop.getByRole("link", { name: "Get Started" })).toHaveAttribute(
      "href",
      "/register",
    );
    expect(screen.getByRole("link", { name: /get started free/i })).toHaveAttribute(
      "href",
      "/register",
    );
  });

  it("A4: a later load after the session ends shows the unauthenticated state", async () => {
    mockedGetSession.mockResolvedValueOnce(session).mockResolvedValueOnce(null);

    render(await HomePage());
    expect(desktopNavigation().getByRole("link", { name: "Dashboard" })).toHaveAttribute(
      "href",
      "/dashboard",
    );

    cleanup();
    render(await HomePage());

    const desktop = desktopNavigation();
    expect(desktop.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(desktop.queryByRole("link", { name: "Dashboard" })).not.toBeInTheDocument();
  });
});
