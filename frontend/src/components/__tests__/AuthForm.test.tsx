const { routerPush } = vi.hoisted(() => ({ routerPush: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: routerPush }),
}));

vi.mock("../../lib/auth", () => ({
  getSession: vi.fn().mockResolvedValue(null),
}));

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AuthForm from "../AuthForm";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("AuthForm", () => {
  beforeEach(() => {
    routerPush.mockClear();
  });

  it("register success creates a session and navigates to the dashboard", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(201, { id: "u1", username: "alice" })),
    );
    const user = userEvent.setup();
    render(<AuthForm mode="register" />);
    await user.type(screen.getByLabelText("Username"), "alice");
    await user.type(screen.getByLabelText("Password"), "s3cret");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/register",
      expect.objectContaining({ method: "POST", credentials: "same-origin" }),
    );
    await waitFor(() => expect(routerPush).toHaveBeenCalledWith("/dashboard"));
  });

  it("keeps the submit button disabled after a successful registration while navigation is pending", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(201, { id: "u1", username: "alice" })),
    );
    routerPush.mockReturnValue(new Promise<void>(() => {}));
    const user = userEvent.setup();
    render(<AuthForm mode="register" />);
    await user.type(screen.getByLabelText("Username"), "alice");
    await user.type(screen.getByLabelText("Password"), "s3cret");
    await user.click(screen.getByRole("button", { name: "Register" }));

    await waitFor(() => expect(routerPush).toHaveBeenCalledWith("/dashboard"));

    const submitButton = screen.getByRole("button", { name: "Register" });
    expect(submitButton).toBeDisabled();

    await user.click(submitButton).catch(() => undefined);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("duplicate username shows a clear error and does not navigate", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(409, { error: "Username already exists" })),
    );
    const user = userEvent.setup();
    render(<AuthForm mode="register" />);
    await user.type(screen.getByLabelText("Username"), "alice");
    await user.type(screen.getByLabelText("Password"), "s3cret");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Username already exists");
    expect(routerPush).not.toHaveBeenCalled();
  });

  it("blank password is rejected without a network call", async () => {
    vi.stubGlobal("fetch", vi.fn());
    const user = userEvent.setup();
    render(<AuthForm mode="register" />);
    await user.type(screen.getByLabelText("Username"), "alice");
    await user.click(screen.getByRole("button", { name: "Register" }));

    expect(screen.getByRole("alert")).toHaveTextContent("Password cannot be blank");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("login success establishes a session and navigates to the dashboard", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(200, { id: "u1", username: "alice" })),
    );
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);
    await user.type(screen.getByLabelText("Username"), "alice");
    await user.type(screen.getByLabelText("Password"), "s3cret");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(fetch).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({ method: "POST" }),
    );
    await waitFor(() => expect(routerPush).toHaveBeenCalledWith("/dashboard"));
  });

  it("wrong password shows a clear error and the user remains unauthenticated", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(jsonResponse(401, { error: "Invalid username or password" })),
    );
    const user = userEvent.setup();
    render(<AuthForm mode="login" />);
    await user.type(screen.getByLabelText("Username"), "alice");
    await user.type(screen.getByLabelText("Password"), "wrong");
    await user.click(screen.getByRole("button", { name: "Log in" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Invalid username or password",
    );
    expect(routerPush).not.toHaveBeenCalled();
  });
});

describe("HomePage", () => {
  it("exposes the public landing page with the approved messaging", async () => {
    const HomePage = (await import("../../app/page")).default;
    const page = await HomePage();

    render(page);
    expect(screen.getByRole("heading", { name: /your tasks, simplified\./i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /get started free/i })).toHaveAttribute("href", "/register");
    expect(screen.getByRole("link", { name: /login/i })).toHaveAttribute("href", "/login");
    const navigation = screen.getByRole("navigation", { name: "Main navigation" });
    const getStarted = within(navigation).getByRole("link", { name: "Get Started" });
    expect(getStarted).toHaveClass("nav-cta");
  });
});