// Task T-044a/T-044b · Spec FR-230–234 · Plan §Frontend plan (TodoList), §Test-First 5 · Contract tasks-api.md
"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import {
  ApiError,
  createTask,
  deleteTask,
  listTasks,
  toggleTask,
  updateTask,
  type TodoItem,
} from "../lib/api";

export default function TodoList({ userId }: { userId: string }) {
  const router = useRouter();
  const [items, setItems] = useState<TodoItem[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftDescription, setDraftDescription] = useState("");
  const [deletingIds, setDeletingIds] = useState<Set<number>>(() => new Set());

  const handleError = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError && err.status === 401) {
        router.push("/login");
        return;
      }
      setError(err instanceof Error ? err.message : "Request failed");
    },
    [router],
  );

  const refresh = useCallback(async () => {
    try {
      const nextItems = await listTasks(userId);
      setItems(nextItems);
      setLoaded(true);
    } catch (err) {
      handleError(err);
    }
  }, [handleError, userId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totalTasks = items.length;
  const completedTasks = items.filter((item) => item.completed).length;
  const pendingTasks = totalTasks - completedTasks;
  const completionRate = totalTasks === 0 ? 0 : Math.round((completedTasks / totalTasks) * 100);

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    setError("");

    const trimmedTitle = title.trim();
    if (!trimmedTitle) {
      setError("Title is required.");
      return;
    }

    try {
      const created = await createTask(userId, trimmedTitle, description.trim() || null);
      setTitle("");
      setDescription("");
      setItems((current) => [created, ...current]);
      await refresh();
    } catch (err) {
      handleError(err);
    }
  }

  async function handleToggle(id: number) {
    setError("");
    try {
      const toggled = await toggleTask(userId, id);
      setItems((current) =>
        current.map((item) => (item.id === id ? toggled : item)),
      );
      await refresh();
    } catch (err) {
      handleError(err);
    }
  }

  async function handleDelete(id: number) {
    setError("");
    setDeletingIds((current) => new Set(current).add(id));
    try {
      await deleteTask(userId, id);
      setItems((current) => current.filter((item) => item.id !== id));
      setDeletingIds((current) => {
        const next = new Set(current);
        next.delete(id);
        return next;
      });
      await refresh();
    } catch (err) {
      setDeletingIds((current) => {
        const next = new Set(current);
        next.delete(id);
        return next;
      });
      handleError(err);
    }
  }

  function beginEdit(item: TodoItem) {
    setEditingId(item.id);
    setDraftTitle(item.title);
    setDraftDescription(item.description ?? "");
    setError("");
  }

  function cancelEdit() {
    setEditingId(null);
    setDraftTitle("");
    setDraftDescription("");
    setError("");
  }

  async function handleSaveEdit() {
    if (editingId === null) {
      return;
    }

    const nextTitle = draftTitle.trim();
    if (!nextTitle) {
      setError("Title is required.");
      return;
    }

    try {
      const updated = await updateTask(userId, editingId, {
        title: nextTitle,
        description: draftDescription.trim() || null,
      });
      setItems((current) =>
        current.map((item) => (item.id === editingId ? updated : item)),
      );
      setEditingId(null);
      setDraftTitle("");
      setDraftDescription("");
    } catch (err) {
      handleError(err);
    }
  }

  return (
    <section aria-label="Todo items" data-responsive className="todo-panel">
      <div className="stats-grid" aria-label="Task overview">
        <div className="stat-card">
          <span className="stat-label">Total</span>
          <strong>{totalTasks}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Completed</span>
          <strong>{completedTasks}</strong>
        </div>
        <div className="stat-card">
          <span className="stat-label">Pending</span>
          <strong>{pendingTasks}</strong>
        </div>
        <div className="stat-card accent">
          <span className="stat-label">Progress</span>
          <strong>{completionRate}%</strong>
        </div>
      </div>

      <form
        aria-label="Add item"
        role="form"
        onSubmit={handleAdd}
        className="responsive-row todo-form"
      >
        <div className="todo-form-fields">
          <label className="todo-field" htmlFor="new-title">
            <span className="sr-only">Add a task</span>
            <input
              id="new-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Add a task"
            />
          </label>
          <label className="todo-field" htmlFor="new-description">
            <span className="sr-only">Description (optional)</span>
            <input
              id="new-description"
              type="text"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              placeholder="Description (optional)"
            />
          </label>
        </div>

        <button type="submit" className="button-primary">Add</button>
      </form>

      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : null}

      {!loaded ? <p className="empty-message">Loading tasks...</p> : null}
      {loaded && items.length === 0 ? <p className="empty-message">No items yet.</p> : null}

      <ul className="todo-list">
        {items.map((item) => (
          <li
            key={item.id}
            className={`responsive-item todo-item${deletingIds.has(item.id) ? " is-deleting" : ""}`}
          >
            {editingId === item.id ? (
              <div className="todo-edit-form">
                <label htmlFor={`edit-title-${item.id}`}>Title</label>
                <input
                  id={`edit-title-${item.id}`}
                  type="text"
                  value={draftTitle}
                  onChange={(event) => setDraftTitle(event.target.value)}
                />

                <label htmlFor={`edit-description-${item.id}`}>
                  Description (optional)
                </label>
                <input
                  id={`edit-description-${item.id}`}
                  type="text"
                  value={draftDescription}
                  onChange={(event) => setDraftDescription(event.target.value)}
                />

                <div className="inline-actions">
                  <button type="button" className="button-primary" onClick={() => void handleSaveEdit()}>
                    Save
                  </button>
                  <button type="button" className="button-secondary" onClick={cancelEdit}>
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <>
                <button
                  type="button"
                  className={`todo-tick${item.completed ? " is-complete" : ""}`}
                  aria-label={`${item.completed ? "Mark" : "Complete"} ${item.title}${item.completed ? " incomplete" : ""}`}
                  aria-pressed={item.completed}
                  onClick={() => void handleToggle(item.id)}
                >
                  <svg viewBox="0 0 24 24" aria-hidden="true">
                    <path d="m5 12 4 4L19 6" />
                  </svg>
                </button>
                <div className="todo-copy">
                  <div className="todo-header-row">
                    <strong className={item.completed ? "is-complete" : undefined}>
                      {item.title}
                    </strong>
                    <span className={`status ${item.completed ? "complete" : "incomplete"}`}>
                      {item.completed ? "complete" : "incomplete"}
                    </span>
                  </div>
                  {item.description ? <p>{item.description}</p> : null}
                </div>

                <div className="item-actions">
                  <button
                    type="button"
                    className="button-secondary"
                    aria-label={`Edit ${item.title}`}
                    onClick={() => beginEdit(item)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className={item.completed ? "button-secondary" : "button-primary"}
                    aria-label={item.completed ? "Mark incomplete" : "Mark complete"}
                    onClick={() => void handleToggle(item.id)}
                  >
                    {item.completed ? "Mark incomplete" : "Mark complete"}
                  </button>
                  <button
                    type="button"
                    className="button-danger"
                    aria-label={`Delete ${item.title}`}
                    onClick={() => void handleDelete(item.id)}
                  >
                    Delete
                  </button>
                </div>
              </>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}