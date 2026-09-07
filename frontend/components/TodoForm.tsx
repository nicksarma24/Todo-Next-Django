"use client";

import { useState } from "react";

import LoadingSpinner from "./LoadingSpinner";

export default function TodoForm({
  onCreate,
}: {
  onCreate: (title: string, description: string) => Promise<void>;
}) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (submitting || !title.trim()) return;

    setSubmitting(true);
    try {
      await onCreate(title.trim(), description.trim());
      setTitle("");
      setDescription("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="todo-form card" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="What needs doing?"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        maxLength={255}
        disabled={submitting}
        required
        aria-label="Todo title"
      />
      <textarea
        placeholder="Description (optional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        disabled={submitting}
        rows={2}
        aria-label="Todo description"
      />
      <div className="form-row">
        <button className="button" type="submit" disabled={submitting || !title.trim()}>
          {submitting ? <LoadingSpinner /> : "Add Todo"}
        </button>
      </div>
    </form>
  );
}
