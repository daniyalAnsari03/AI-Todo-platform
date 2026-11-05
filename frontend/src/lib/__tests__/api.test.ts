// Task T-036 (tests) · Spec FR-221, FR-233 · Plan §Frontend plan (api.ts rewrite), §Test-First 5 · Contract tasks-api.md, auth-jwt.md §Frontend usage
const hoisted = vi.hoisted(() => ({
  getToken: vi.fn(),
  invalidateToken: vi.fn(),
  locationAssign: vi.fn(),
}));

vi.mock("../token", () => hoisted);

import {
  ApiError,
  createTask,
  deleteTask,
  getTask,
  listTasks,
  toggleTask,
  updateTask,
} from "../api";

const TOKEN = "tok-1";

const sampleTask = {
  id: 7,
  user_id: "usr_abc123",
  title: "Buy milk",
  description: "2% or oat",
  completed: false,
  created_at: "2026-10-24T12:00:00.000Z",
  updated_at: "2026-10-24T12:00:00.000Z",
};

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function ok204() {
  return new Response(null, { status: 204 });
}

function unauthorized() {
  return new Response(JSON.stringify({ detail: "Not authenticated" }), {
    status: 401,
    headers: { "content-type": "application/json" },
  });
}

const fetchMock = vi.fn();

describe("task API client", () => {
  beforeEach(() => {
    hoisted.getToken.mockReset().mockResolvedValue(TOKEN);
    hoisted.invalidateToken.mockReset();
    hoisted.locationAssign.mockReset();
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    Object.defineProperty(window, "location", {
      configurable: true,
      value: { assign: hoisted.locationAssign, href: "http://localhost/" },
    });
  });

  describe("always sends Authorization: Bearer with the correct method and path", () => {
    it("listTasks → GET /api/usr_abc123/tasks", async () => {
      fetchMock.mockResolvedValue(
        jsonResponse({ items: [sampleTask] }),
      );

      const items = await listTasks("usr_abc123");

      expect(items).toEqual([sampleTask]);
      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/usr_abc123/tasks");
      expect(init.method).toBe("GET");
      expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
    });

    it("createTask → POST /api/usr_abc123/tasks with a JSON body", async () => {
      fetchMock.mockResolvedValue(jsonResponse(sampleTask, 201));

      const created = await createTask("usr_abc123", "Buy milk", "2% or oat");

      expect(created).toEqual(sampleTask);
      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/usr_abc123/tasks");
      expect(init.method).toBe("POST");
      expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
      expect(init.headers["Content-Type"]).toBe("application/json");
      expect(JSON.parse(init.body)).toEqual({
        title: "Buy milk",
        description: "2% or oat",
      });
    });

    it("createTask sends a null description when none is given", async () => {
      fetchMock.mockResolvedValue(
        jsonResponse({ ...sampleTask, description: null }, 201),
      );

      await createTask("usr_abc123", "Only a title");

      const [, init] = fetchMock.mock.calls[0];
      expect(JSON.parse(init.body)).toEqual({
        title: "Only a title",
        description: null,
      });
    });

    it("getTask → GET /api/usr_abc123/tasks/7", async () => {
      fetchMock.mockResolvedValue(jsonResponse(sampleTask));

      await getTask("usr_abc123", 7);

      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/usr_abc123/tasks/7");
      expect(init.method).toBe("GET");
      expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
    });

    it("updateTask → PUT /api/usr_abc123/tasks/7 with a JSON body", async () => {
      fetchMock.mockResolvedValue(
        jsonResponse({ ...sampleTask, title: "Buy oat milk" }),
      );

      await updateTask("usr_abc123", 7, {
        title: "Buy oat milk",
        description: "2% or oat",
      });

      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/usr_abc123/tasks/7");
      expect(init.method).toBe("PUT");
      expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
      expect(JSON.parse(init.body)).toEqual({
        title: "Buy oat milk",
        description: "2% or oat",
      });
    });

    it("deleteTask → DELETE /api/usr_abc123/tasks/7", async () => {
      fetchMock.mockResolvedValue(ok204());

      await expect(deleteTask("usr_abc123", 7)).resolves.toBeUndefined();

      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/usr_abc123/tasks/7");
      expect(init.method).toBe("DELETE");
      expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
    });

    it("toggleTask → PATCH /api/usr_abc123/tasks/7/complete", async () => {
      fetchMock.mockResolvedValue(jsonResponse({ ...sampleTask, completed: true }));

      await toggleTask("usr_abc123", 7);

      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("/api/usr_abc123/tasks/7/complete");
      expect(init.method).toBe("PATCH");
      expect(init.headers.Authorization).toBe(`Bearer ${TOKEN}`);
    });
  });

  describe("401 handling (contract auth-jwt.md §Frontend usage)", () => {
    it("invalidates the token, silently re-fetches it once, retries the call once and succeeds", async () => {
      fetchMock
        .mockResolvedValueOnce(unauthorized())
        .mockResolvedValueOnce(jsonResponse({ items: [sampleTask] }));

      const items = await listTasks("usr_abc123");

      expect(items).toEqual([sampleTask]);
      expect(hoisted.invalidateToken).toHaveBeenCalledTimes(1);
      expect(hoisted.getToken).toHaveBeenCalledTimes(2);
      const taskCalls = fetchMock.mock.calls.filter(
        ([url]) => url === "/api/usr_abc123/tasks",
      );
      expect(taskCalls).toHaveLength(2);
    });

    it("redirects to /login when the retried call is still 401 (no infinite loop)", async () => {
      fetchMock.mockResolvedValue(unauthorized());

      await expect(listTasks("usr_abc123")).rejects.toMatchObject({
        status: 401,
      });

      expect(hoisted.invalidateToken).toHaveBeenCalledTimes(1);
      expect(hoisted.getToken).toHaveBeenCalledTimes(2);
      expect(hoisted.locationAssign).toHaveBeenCalledWith("/login");
      const taskCalls = fetchMock.mock.calls.filter(
        ([url]) => url === "/api/usr_abc123/tasks",
      );
      expect(taskCalls).toHaveLength(2);
    });

    it("redirects to /login when the one silent token re-fetch itself fails", async () => {
      fetchMock.mockResolvedValueOnce(unauthorized());
      hoisted.getToken
        .mockResolvedValueOnce(TOKEN)
        .mockRejectedValueOnce(new Error("token expired"));

      await expect(createTask("usr_abc123", "x")).rejects.toBeInstanceOf(
        ApiError,
      );

      expect(hoisted.locationAssign).toHaveBeenCalledWith("/login");
    });

    it("does not retry non-401 failures", async () => {
      fetchMock.mockResolvedValue(jsonResponse({ detail: "nope" }, 403));

      await expect(listTasks("usr_abc123")).rejects.toMatchObject({
        status: 403,
      });

      expect(hoisted.invalidateToken).not.toHaveBeenCalled();
      expect(hoisted.locationAssign).not.toHaveBeenCalled();
    });
  });
});
