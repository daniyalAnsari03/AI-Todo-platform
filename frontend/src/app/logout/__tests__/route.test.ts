const { authMock } = vi.hoisted(() => ({
  authMock: {
    api: {
      signOut: vi.fn().mockResolvedValue({ success: true }),
    },
  },
}));

vi.mock("../../../../auth", () => ({ auth: authMock }));

import { NextRequest } from "next/server";
import { describe, expect, it, vi } from "vitest";

import { GET } from "../route";

describe("GET /logout", () => {
  it("ends the session and redirects to /login", async () => {
    const request = new NextRequest("http://localhost:3000/logout");

    const response = await GET(request);

    expect(authMock.api.signOut).toHaveBeenCalledWith({ headers: request.headers });
    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe("http://localhost:3000/login");
  });
});