// Task T-041 · Spec FR-210–213, FR-230–234 · Plan §Frontend plan (task API), §Auth plan (frontend) · Contract tasks-api.md, auth-jwt.md §Frontend usage
import { getToken, invalidateToken } from "./token";

export type TodoItem = {
  id: number;
  user_id: string;
  title: string;
  description: string | null;
  completed: boolean;
  created_at: string;
  updated_at: string;
};

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function normalizeHeaders(init?: RequestInit): Record<string, string> {
  if (!init?.headers) {
    return {};
  }

  if (init.headers instanceof Headers) {
    return Object.fromEntries(init.headers.entries());
  }

  if (Array.isArray(init.headers)) {
    return Object.fromEntries(init.headers);
  }

  return Object.fromEntries(
    Object.entries(init.headers as Record<string, string>).map(([key, value]) => [
      key,
      String(value),
    ]),
  );
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    body = null;
  }

  if (!response.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? String((body as { detail?: string }).detail ?? "Request failed")
        : typeof body === "object" && body !== null && "error" in body
          ? String((body as { error?: string }).error ?? "Request failed")
          : "Request failed";
    throw new ApiError(detail, response.status);
  }

  return body as T;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let retried = false;

  while (true) {
    let token: string;
    try {
      token = await getToken();
    } catch {
      window.location.assign("/login");
      throw new ApiError("Unauthorized", 401);
    }

    const headers = normalizeHeaders(init);
    headers.Authorization = `Bearer ${token}`;

    const response = await fetch(path, {
      method: init?.method ?? "GET",
      credentials: "same-origin",
      ...init,
      headers,
    });

    if (response.status === 401 && !retried) {
      invalidateToken();
      retried = true;
      continue;
    }

    if (response.status === 401) {
      window.location.assign("/login");
      throw new ApiError("Unauthorized", 401);
    }

    return parseResponse<T>(response);
  }
}

export async function listTasks(userId: string): Promise<TodoItem[]> {
  const result = await request<{ items: TodoItem[] }>(`/api/${userId}/tasks`);
  return result.items;
}

export async function getTask(userId: string, taskId: number): Promise<TodoItem> {
  return request<TodoItem>(`/api/${userId}/tasks/${taskId}`);
}

export async function createTask(
  userId: string,
  title: string,
  description?: string | null,
): Promise<TodoItem> {
  return request<TodoItem>(`/api/${userId}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title,
      description: description ?? null,
    }),
  });
}

export async function updateTask(
  userId: string,
  taskId: number,
  changes: Partial<Pick<TodoItem, "title" | "description">>,
): Promise<TodoItem> {
  return request<TodoItem>(`/api/${userId}/tasks/${taskId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(changes),
  });
}

export async function deleteTask(userId: string, taskId: number): Promise<void> {
  await request<void>(`/api/${userId}/tasks/${taskId}`, { method: "DELETE" });
}

export async function toggleTask(userId: string, taskId: number): Promise<TodoItem> {
  return request<TodoItem>(`/api/${userId}/tasks/${taskId}/complete`, {
    method: "PATCH",
  });
}