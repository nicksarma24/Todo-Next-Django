"use client";

import { useState } from "react";

import type { Todo } from "@/lib/types";
import LoadingSpinner from "./LoadingSpinner";

export default function TodoItem({
  todo,
  onToggle,
  onUpdate,
  onDelete,
}: {
  todo: Todo;
  onToggle: (id: number, completed: boolean) => Promise<void>;
  onUpdate: (id: number, data: { title: string; description: string }) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(todo.title);
  const [description, setDescription] = useState(todo.description);
  const [busy, setBusy] = useState<"toggle" | "save" | "delete" | null>(null);

  async function handleToggle() {
    if (busy) return;
    setBusy("toggle");
    try {
      await onToggle(todo.id, !todo.completed);
    } finally {
      setBusy(null);
    }
  }

  async function handleSave() {
    if (busy || !title.trim()) return;
    setBusy("save");
    try {
      await onUpdate(todo.id, { title: title.trim(), description: description.trim() });
      setIsEditing(false);
    } finally {
      setBusy(null);
    }
  }

  async function handleDelete() {
    if (busy) return;
    setBusy("delete");
    try {
      await onDelete(todo.id);
    } finally {
      setBusy(null);
    }
  }

  if (isEditing) {
    return (
      <li className="todo-item card">
        <div className="todo-content todo-form" style={{ marginBottom: 0 }}>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={255}
            disabled={busy === "save"}
            aria-label="Edit title"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={busy === "save"}
            rows={2}
            aria-label="Edit description"
          />
          <div className="form-row">
            <button
              className="button"
              type="button"
              onClick={handleSave}
              disabled={busy === "save" || !title.trim()}
            >
              {busy === "save" ? <LoadingSpinner /> : "Save"}
            </button>
            <button
              className="button secondary"
              type="button"
              onClick={() => {
                setTitle(todo.title);
                setDescription(todo.description);
                setIsEditing(false);
              }}
              disabled={busy === "save"}
            >
              Cancel
            </button>
          </div>
        </div>
      </li>
    );
  }

  return (
    <li className={`todo-item card${todo.completed ? " completed" : ""}`}>
      <input
        type="checkbox"
        checked={todo.completed}
        onChange={handleToggle}
        disabled={busy !== null}
        aria-label={todo.completed ? "Mark as not completed" : "Mark as completed"}
      />
      <div className="todo-content">
        <div className="todo-title">{todo.title}</div>
        {todo.description && <div className="todo-description">{todo.description}</div>}
      </div>
      <div className="todo-actions">
        {busy === "toggle" ? (
          <LoadingSpinner dark />
        ) : (
          <>
            <button
              className="button secondary"
              type="button"
              onClick={() => setIsEditing(true)}
              disabled={busy !== null}
            >
              Edit
            </button>
            <button
              className="button danger"
              type="button"
              onClick={handleDelete}
              disabled={busy !== null}
            >
              {busy === "delete" ? <LoadingSpinner dark /> : "Delete"}
            </button>
          </>
        )}
      </div>
    </li>
  );
}
