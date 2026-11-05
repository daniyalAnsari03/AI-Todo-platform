// Task T-037 (rewritten tests) · Spec US4-1–6 (FR-230–234) · Plan §Frontend plan (TodoList), §Test-First 5, §OQ-5 · Contract tasks-api.md
const { routerPush } = vi.hoisted(() => ({ routerPush: vi.fn() }));

const router = { push: routerPush };

vi.mock("next/navigation", () => ({
  useRouter: () => router,
}));

const api = vi.hoisted(() => {
  class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  }
  return {
    ApiError,
    listTasks: vi.fn(),
    createTask: vi.fn(),
    getTask: vi.fn(),
    updateTask: vi.fn(),
    toggleTask: vi.fn(),
    deleteTask: vi.fn(),
  };
});

vi.mock("../../lib/api", () => api);

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TodoList from "../TodoList";

const USER_ID = "usr_abc123";

const milk = {
  id: 1,
  user_id: USER_ID,
  title: "Buy milk",
  description: "2% or oat",
  completed: false,
  created_at: "2026-10-24T12:00:00.000Z",
  updated_at: "2026-10-24T12:00:00.000Z",
};

const plants = {
  ...milk,
  id: 2,
  title: "Water plants",
  description: null,
  completed: true,
};

describe("TodoList", () => {
  beforeEach(() => {
    routerPush.mockClear();
    const keys = [
      "listTasks",
      "createTask",
      "getTask",
      "updateTask",
      "toggleTask",
      "deleteTask",
    ] as const satisfies ReadonlyArray<keyof typeof api>;

    for (const key of keys) {
      api[key].mockReset();
    }
    api.listTasks.mockResolvedValue([]);
  });

  it("list rows show title, description and status indicator", async () => {
    api.listTasks.mockResolvedValue([milk, plants]);
    render(<TodoList userId={USER_ID} />);

    expect(await screen.findByText("Buy milk")).toBeInTheDocument();
    expect(screen.getByText("2% or oat")).toBeInTheDocument();
    expect(screen.getByText("Water plants")).toBeInTheDocument();
    expect(screen.getAllByText("incomplete").length).toBeGreaterThan(0);
    expect(screen.getAllByText("complete").length).toBeGreaterThan(0);
    expect(api.listTasks).toHaveBeenCalledWith(USER_ID);
  });

  it("shows an empty-list message and the two-field add form", async () => {
    api.listTasks.mockResolvedValue([plants]);
    render(<TodoList userId={USER_ID} />);

    expect(await screen.findByText("Water plants")).toBeInTheDocument();
    const form = screen.getByRole("form", { name: "Add item" });
    expect(form).toBeInTheDocument();
    expect(screen.getByLabelText("Add a task")).toBeInTheDocument();
    expect(screen.getByLabelText("Description (optional)")).toBeInTheDocument();
    expect(form.querySelectorAll("input")).toHaveLength(2);
    expect(form.querySelector(".todo-form-fields")).toBeInTheDocument();
  });

  it("adds with title and description through the API and refreshes", async () => {
    api.listTasks.mockResolvedValueOnce([]).mockResolvedValueOnce([milk]);
    api.createTask.mockResolvedValue(milk);
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.type(screen.getByLabelText("Add a task"), "Buy milk");
    await user.type(
      screen.getByLabelText("Description (optional)"),
      "2% or oat",
    );
    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(api.createTask).toHaveBeenCalledWith(
      USER_ID,
      "Buy milk",
      "2% or oat",
    );
    expect(api.listTasks).toHaveBeenCalledTimes(2);
    expect(await screen.findByText("Buy milk")).toBeInTheDocument();
  });

  it("blocks an empty title client-side with a visible message and no API call", async () => {
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(screen.getByRole("button", { name: "Add" }));

    expect(screen.getByRole("alert")).toHaveTextContent(/title/i);
    expect(api.createTask).not.toHaveBeenCalled();
  });

  it("edits an item inline with pre-filled fields; Save calls updateTask with both fields", async () => {
    api.listTasks.mockResolvedValue([milk]);
    api.updateTask.mockResolvedValue({
      ...milk,
      title: "Buy oat milk",
      description: "barista oat",
    });
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(
      await screen.findByRole("button", { name: `Edit ${milk.title}` }),
    );
    const titleInput = screen.getByDisplayValue("Buy milk");
    const descriptionInput = screen.getByDisplayValue("2% or oat");
    await user.clear(titleInput);
    await user.type(titleInput, "Buy oat milk");
    await user.clear(descriptionInput);
    await user.type(descriptionInput, "barista oat");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(api.updateTask).toHaveBeenCalledWith(USER_ID, 1, {
      title: "Buy oat milk",
      description: "barista oat",
    });
    expect(screen.getAllByText("Buy oat milk").length).toBeGreaterThan(0);
  });

  it("cancels an edit and reverts without calling the API", async () => {
    api.listTasks.mockResolvedValue([milk]);
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(
      await screen.findByRole("button", { name: `Edit ${milk.title}` }),
    );
    await user.type(screen.getByDisplayValue("Buy milk"), " changed");
    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(api.updateTask).not.toHaveBeenCalled();
    expect(screen.getAllByText("Buy milk").length).toBeGreaterThan(0);
    expect(screen.queryByDisplayValue("Buy milk changed")).not.toBeInTheDocument();
  });

  it("toggles an incomplete item to complete (true direction)", async () => {
    api.listTasks.mockResolvedValueOnce([milk]).mockResolvedValueOnce([
      { ...milk, completed: true },
    ]);
    api.toggleTask.mockResolvedValue({ ...milk, completed: true });
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(
      await screen.findByRole("button", { name: "Mark complete" }),
    );

    expect(api.toggleTask).toHaveBeenCalledWith(USER_ID, 1);
    await waitFor(() => expect(api.listTasks).toHaveBeenCalledTimes(2));
  });

  it("toggles completion with the round tick control", async () => {
    api.listTasks.mockResolvedValueOnce([milk]).mockResolvedValueOnce([
      { ...milk, completed: true },
    ]);
    api.toggleTask.mockResolvedValue({ ...milk, completed: true });
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(await screen.findByRole("button", { name: "Complete Buy milk" }));

    expect(api.toggleTask).toHaveBeenCalledWith(USER_ID, milk.id);
  });

  it("toggles a completed item back to incomplete (false direction)", async () => {
    api.listTasks.mockResolvedValueOnce([plants]).mockResolvedValueOnce([
      { ...plants, completed: false },
    ]);
    api.toggleTask.mockResolvedValue({ ...plants, completed: false });
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(
      await screen.findByRole("button", { name: "Mark incomplete" }),
    );

    expect(api.toggleTask).toHaveBeenCalledWith(USER_ID, 2);
    expect(
      await screen.findByRole("button", { name: "Mark complete" }),
    ).toBeInTheDocument();
  });

  it("deletes an item through the API and refreshes", async () => {
    api.listTasks.mockResolvedValueOnce([milk]).mockResolvedValueOnce([]);
    api.deleteTask.mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<TodoList userId={USER_ID} />);

    await user.click(
      await screen.findByRole("button", { name: `Delete ${milk.title}` }),
    );

    expect(api.deleteTask).toHaveBeenCalledWith(USER_ID, 1);
    expect(await screen.findByText("No items yet.")).toBeInTheDocument();
  });

  it("redirects to /login when the API rejects with 401", async () => {
    api.listTasks.mockRejectedValue(new api.ApiError("Unauthorized", 401));
    render(<TodoList userId={USER_ID} />);

    await waitFor(() => expect(routerPush).toHaveBeenCalledWith("/login"));
  });

  it("has responsive hooks so add-form controls and rows can stack without horizontal scroll", async () => {
    api.listTasks.mockResolvedValue([milk]);
    const { container } = render(<TodoList userId={USER_ID} />);

    await screen.findByText("Buy milk");
    expect(container.querySelector("[data-responsive]")).not.toBeNull();
    const form = screen.getByRole("form", { name: "Add item" });
    expect(form.classList.contains("responsive-row")).toBe(true);
    expect(container.querySelector(".responsive-item")).not.toBeNull();
  });
});
