// Task T-040 (T-035 failing tests) · Spec FR-221, FR-229, FR-233 · Plan §Frontend plan (token.ts), §OQ-3 (memory-only) · Contract auth-jwt.md §Frontend usage
let cachedToken: string | null = null;
let inflight: Promise<string> | null = null;

export function invalidateToken(): void {
  cachedToken = null;
  inflight = null;
}

export function getToken(): Promise<string> {
  if (cachedToken !== null) {
    return Promise.resolve(cachedToken);
  }
  if (inflight === null) {
    inflight = (async () => {
      try {
        const response = await fetch("/api/auth/token", { method: "GET" });
        if (!response.ok) {
          throw new Error("Token endpoint returned an error");
        }
        const body = (await response.json()) as { token?: unknown };
        if (typeof body.token !== "string") {
          throw new Error("Token endpoint returned no token");
        }
        cachedToken = body.token;
        return cachedToken;
      } finally {
        inflight = null;
      }
    })();
  }
  return inflight;
}
