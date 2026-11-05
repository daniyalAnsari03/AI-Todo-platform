import { NextRequest, NextResponse } from "next/server";
import { describe, expect, it, vi } from "vitest";

import {
  handleAuthPost,
  type AuthDelegator,
} from "../auth-handler";

type AuthLike = {
  api: {
    signUpEmail: ReturnType<typeof vi.fn> &
      AuthDelegator["api"]["signUpEmail"];
    signInEmail: ReturnType<typeof vi.fn> &
      AuthDelegator["api"]["signInEmail"];
    signOut: ReturnType<typeof vi.fn> & AuthDelegator["api"]["signOut"];
  };
};

function makeAuth(): AuthLike {
  return {
    api: {
      signUpEmail: vi.fn(),
      signInEmail: vi.fn(),
      signOut: vi.fn().mockResolvedValue({ success: true }),
    },
  };
}

function postRequest(path: string, body?: unknown): NextRequest {
  return new NextRequest(`http://localhost:3000${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

describe("handleAuthPost", () => {
  it("register creates an account, starts a session, and returns 201 with id and username", async () => {
    const auth = makeAuth();
    auth.api.signUpEmail.mockResolvedValue({
      token: "tok",
      user: { id: "u1", name: "alice" },
    });

    const response = await handleAuthPost(auth, postRequest("/api/auth/register", {
      username: "alice",
      password: "s3cret",
    }));

    expect(auth.api.signUpEmail).toHaveBeenCalledWith({
      body: { name: "alice", email: "alice@todo.local", password: "s3cret" },
    });
    expect(response.status).toBe(201);
    expect(await response.json()).toEqual({ id: "u1", username: "alice" });
  });

  it("register with a duplicate username returns 409 and creates no account", async () => {
    const auth = makeAuth();
    auth.api.signUpEmail.mockRejectedValue(new Error("already exists"));

    const response = await handleAuthPost(auth, postRequest("/api/auth/register", {
      username: "alice",
      password: "s3cret",
    }));

    expect(response.status).toBe(409);
    expect((await response.json()).error).toMatch(/exists/i);
  });

  it("register with a blank password returns 400", async () => {
    const auth = makeAuth();
    const response = await handleAuthPost(auth, postRequest("/api/auth/register", {
      username: "alice",
      password: "",
    }));

    expect(response.status).toBe(400);
    expect(auth.api.signUpEmail).not.toHaveBeenCalled();
  });

  it("register with a blank username returns 400", async () => {
    const auth = makeAuth();
    const response = await handleAuthPost(auth, postRequest("/api/auth/register", {
      username: "   ",
      password: "s3cret",
    }));

    expect(response.status).toBe(400);
    expect(auth.api.signUpEmail).not.toHaveBeenCalled();
  });

  it("login with correct credentials returns 200 and the session user", async () => {
    const auth = makeAuth();
    auth.api.signInEmail.mockResolvedValue({
      token: "tok",
      user: { id: "u1", name: "alice" },
    });

    const response = await handleAuthPost(auth, postRequest("/api/auth/login", {
      username: "alice",
      password: "s3cret",
    }));

    expect(auth.api.signInEmail).toHaveBeenCalledWith({
      body: { email: "alice@todo.local", password: "s3cret" },
    });
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ id: "u1", username: "alice" });
  });

  it("login with wrong credentials returns 401 and keeps the user unauthenticated", async () => {
    const auth = makeAuth();
    auth.api.signInEmail.mockRejectedValue(new Error("invalid"));

    const response = await handleAuthPost(auth, postRequest("/api/auth/login", {
      username: "alice",
      password: "wrong",
    }));

    expect(response.status).toBe(401);
    expect((await response.json()).error).toMatch(/invalid/i);
  });

  it("logout ends the session and returns 204", async () => {
    const auth = makeAuth();
    const request = postRequest("/api/auth/logout");

    const response = await handleAuthPost(auth, request);

    expect(auth.api.signOut).toHaveBeenCalledWith({ headers: request.headers });
    expect(response.status).toBe(204);
  });
});