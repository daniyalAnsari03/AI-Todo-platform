// Deployment readiness: backend rewrite destination must come from the
// server-side env var BACKEND_URL with a local default so that local behavior
// stays identical when BACKEND_URL is unset. Note: NEXT_PUBLIC_* vars are
// insufficient because next.config.js rewrites are evaluated on the server.
import { afterEach, describe, expect, it, vi } from "vitest";

const ORIGINAL_ENV = { ...process.env };

vi.resetModules();

async function loadRewrites() {
  vi.resetModules();
  const mod = (await import("../../../next.config.js")) as {
    default: {
      rewrites: () => Promise<
        Array<{ source: string; destination: string }>
      > | Array<{ source: string; destination: string }>;
    };
  };
  const config = mod.default ?? mod;
  const result = await config.rewrites();
  return Array.isArray(result) ? result : result;
}

describe("next.config.js backend rewrite destination", () => {
  afterEach(() => {
    process.env = { ...ORIGINAL_ENV };
  });

  it("defaults to the local backend when BACKEND_URL is unset (unchanged local behavior)", async () => {
    delete process.env.BACKEND_URL;
    const rules = await loadRewrites();
    const destinations = rules.map((r) => r.destination);
    expect(destinations.every((d) =>
      d.startsWith("http://127.0.0.1:8000/api/"),
    )).toBe(true);
  });

  it("derives destinations from the server-side BACKEND_URL env var, trailing slash stripped", async () => {
    process.env.BACKEND_URL = "https://todo-api.onrender.com/";
    const rules = await loadRewrites();
    const destinations = rules.map((r) => r.destination);
    expect(
      destinations.every((d) =>
        d.startsWith("https://todo-api.onrender.com/api/"),
      ),
    ).toBe(true);
    expect(destinations.some((d) => d.endsWith("/"))).toBe(false);
  });

  it("keeps the four existing proxy routes unchanged", async () => {
    delete process.env.BACKEND_URL;
    const rules = await loadRewrites();
    expect(rules.map((r) => r.source)).toEqual([
      "/api/:userId/chat",
      "/api/:userId/chatkit",
      "/api/:userId/tasks",
      "/api/:userId/tasks/:path*",
    ]);
  });
});
