// Task T-035 · Spec FR-221, FR-229, FR-233 · Plan §Frontend plan (token.ts), §Test-First 5, §OQ-3 · Contract auth-jwt.md §Frontend usage
const tokenOk = (token: string) =>
  new Response(JSON.stringify({ token }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

import { getToken, invalidateToken } from "../token";

describe("getToken", () => {
  beforeEach(() => {
    invalidateToken();
    fetchMock.mockReset();
  });

  it("fetches GET /api/auth/token once for a burst of concurrent calls (single-flight)", async () => {
    fetchMock.mockResolvedValue(tokenOk("tok-1"));

    const [first, second] = await Promise.all([getToken(), getToken()]);

    expect(first).toBe("tok-1");
    expect(second).toBe("tok-1");
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe("/api/auth/token");
    expect(fetchMock.mock.calls[0][1]?.method).toBe("GET");
  });

  it("memoizes the token in memory: a later call does not fetch again", async () => {
    fetchMock.mockResolvedValue(tokenOk("tok-2"));

    await expect(getToken()).resolves.toBe("tok-2");
    fetchMock.mockClear();

    await expect(getToken()).resolves.toBe("tok-2");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fetches again after invalidateToken() clears the in-memory token", async () => {
    fetchMock.mockImplementation(() => Promise.resolve(tokenOk("tok-3")));

    await expect(getToken()).resolves.toBe("tok-3");
    invalidateToken();
    await expect(getToken()).resolves.toBe("tok-3");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("never persists the token to localStorage or sessionStorage", async () => {
    fetchMock.mockResolvedValue(tokenOk("tok-4"));

    await getToken();

    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(0);
  });

  it("rejects and does not memoize when the token endpoint returns an error", async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ error: "boom" }), { status: 500 }),
    );

    await expect(getToken()).rejects.toBeInstanceOf(Error);
    expect(fetchMock).toHaveBeenCalledTimes(1);

    invalidateToken();
    fetchMock.mockResolvedValue(tokenOk("tok-5"));
    await expect(getToken()).resolves.toBe("tok-5");
  });
});
