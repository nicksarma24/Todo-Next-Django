"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, todosApi } from "@/lib/api";
import type { Todo, TodoFilterValue } from "@/lib/types";
import TodoForm from "./TodoForm";
import TodoItem from "./TodoItem";
import EmptyState from "./EmptyState";
import ErrorBanner from "./ErrorBanner";
import LoadingSpinner from "./LoadingSpinner";

export default function TodoDashboard({
  userName,
  userEmail,
  userPicture,
}: {
  userName: string;
  userEmail: string;
  userPicture?: string;
}) {
  const [todos, setTodos] = useState<Todo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [filter, setFilter] = useState<TodoFilterValue>("all");
  const [search, setSearch] = useState("");

  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function showToast(message: string) {
    setToast(message);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2500);
  }

  const loadTodos = useCallback(async (currentFilter: TodoFilterValue, currentSearch: string) => {
    setLoading(true);
    setError(null);
    try {
      const params =
        currentFilter === "all" ? {} : { completed: currentFilter === "completed" };
      const data = await todosApi.list({ ...params, search: currentSearch || undefined });
      setTodos(data.results);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load todos.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Debounce search so we don't fire a request on every keystroke.
  useEffect(() => {
    const handle = setTimeout(() => {
      loadTodos(filter, search);
    }, 300);
    return () => clearTimeout(handle);
  }, [filter, search, loadTodos]);

  async function handleCreate(title: string, description: string) {
    try {
      const created = await todosApi.create({ title, description });
      // Only splice it into the visible list if it matches the current filter.
      if (filter === "all" || (filter === "completed") === created.completed) {
        setTodos((prev) => [created, ...prev]);
      }
      showToast("Todo added");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create todo.");
    }
  }

  async function handleToggle(id: number, completed: boolean) {
    try {
      const updated = await todosApi.update(id, { completed });
      applyUpdateOrRemoveIfFiltered(updated);
      showToast(completed ? "Marked complete" : "Marked incomplete");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update todo.");
    }
  }

  async function handleUpdate(id: number, data: { title: string; description: string }) {
    try {
      const updated = await todosApi.update(id, data);
      applyUpdateOrRemoveIfFiltered(updated);
      showToast("Todo updated");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update todo.");
    }
  }

  function applyUpdateOrRemoveIfFiltered(updated: Todo) {
    setTodos((prev) => {
      const stillMatchesFilter =
        filter === "all" || (filter === "completed") === updated.completed;
      if (!stillMatchesFilter) {
        return prev.filter((t) => t.id !== updated.id);
      }
      return prev.map((t) => (t.id === updated.id ? updated : t));
    });
  }

  async function handleDelete(id: number) {
    const previous = todos;
    setTodos((prev) => prev.filter((t) => t.id !== id));
    try {
      await todosApi.remove(id);
      showToast("Todo deleted");
    } catch (err) {
      setTodos(previous); // roll back optimistic removal
      setError(err instanceof ApiError ? err.message : "Failed to delete todo.");
    }
  }

  return (
    <>
      <div className="header-bar">
        <h1>Todo</h1>
        <div className="user-row">
          {userPicture && <img src={userPicture} alt={userName} />}
          <div>
            <div>{userName}</div>
            {userEmail && <div className="user-email">{userEmail}</div>}
          </div>
          <a className="button secondary" href="/auth/logout">
            Log Out
          </a>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <TodoForm onCreate={handleCreate} />

      <div className="filter-row">
        {(["all", "active", "completed"] as TodoFilterValue[]).map((value) => (
          <button
            key={value}
            type="button"
            className={`chip${filter === value ? " active" : ""}`}
            onClick={() => setFilter(value)}
          >
            {value[0].toUpperCase() + value.slice(1)}
          </button>
        ))}
        <input
          type="search"
          placeholder="Search todos…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search todos"
        />
      </div>

      {loading ? (
        <div className="center-spinner">
          <LoadingSpinner dark />
        </div>
      ) : todos.length === 0 ? (
        <EmptyState
          message={
            search || filter !== "all"
              ? "No todos match your filters."
              : "No todos yet — add your first one above."
          }
        />
      ) : (
        <ul className="todo-list">
          {todos.map((todo) => (
            <TodoItem
              key={todo.id}
              todo={todo}
              onToggle={handleToggle}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </ul>
      )}

      {toast && <div className="toast">{toast}</div>}
    </>
  );
}
