import type { PaginatedResponse, Todo } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Fetches a fresh Auth0 access token from our own same-origin route. */
async function getAccessToken(): Promise<string> {
  const response = await fetch("/api/token", { cache: "no-store" });
  if (!response.ok) {
    throw new ApiError(response.status, "Your session has expired. Please log in again.");
  }
  const data = await response.json();
  return data.accessToken as string;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  let token: string;
  try {
    token = await getAccessToken();
  } catch {
    throw new ApiError(401, "You need to be logged in to do that.");
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...options.headers,
      },
    });
  } catch {
    throw new ApiError(0, "Network error — please check your connection and try again.");
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // Some error responses may not have a JSON body; that's fine.
  }

  if (!response.ok) {
    const detail =
      (body as { detail?: string } | null)?.detail ?? messageForStatus(response.status);
    throw new ApiError(response.status, detail);
  }

  return body as T;
}

function messageForStatus(status: number): string {
  switch (status) {
    case 400:
      return "That request wasn't valid — please check the form and try again.";
    case 401:
      return "You need to be logged in to do that.";
    case 403:
      return "You don't have permission to do that.";
    case 404:
      return "That todo could not be found. It may have been deleted.";
    default:
      return "Something went wrong. Please try again.";
  }
}

export interface TodoListParams {
  completed?: boolean;
  search?: string;
}

function buildQuery(params: TodoListParams): string {
  const query = new URLSearchParams();
  if (params.completed !== undefined) query.set("completed", String(params.completed));
  if (params.search) query.set("search", params.search);
  const qs = query.toString();
  return qs ? `?${qs}` : "";
}

export const todosApi = {
  list(params: TodoListParams = {}): Promise<PaginatedResponse<Todo>> {
    return request<PaginatedResponse<Todo>>(`/todos/${buildQuery(params)}`);
  },

  create(data: { title: string; description?: string }): Promise<Todo> {
    return request<Todo>("/todos/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  update(id: number, data: Partial<Pick<Todo, "title" | "description" | "completed">>): Promise<Todo> {
    return request<Todo>(`/todos/${id}/`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  remove(id: number): Promise<void> {
    return request<void>(`/todos/${id}/`, { method: "DELETE" });
  },
};
