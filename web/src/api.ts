import type { Note, NotePage, Session, Visibility } from "./types";

const BASE_URL = import.meta.env?.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

let token: string | null = null;

export function setToken(value: string | null): void {
  token = value;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("content-type", "application/json");
  if (token) {
    headers.set("authorization", `Bearer ${token}`);
  }
  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

export const api = {
  register(email: string, password: string): Promise<{ id: number; email: string }> {
    return request("/users/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  login(email: string, password: string): Promise<Session> {
    return request("/users/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  listNotes(page = 0, limit = 25): Promise<NotePage> {
    return request(`/notes?limit=${limit}&offset=${page * limit}`);
  },

  createNote(title: string, body: string, visibility: Visibility = "private"): Promise<Note> {
    return request("/notes", {
      method: "POST",
      body: JSON.stringify({ title, body, visibility }),
    });
  },

  updateNote(id: number, patch: { title?: string; body?: string }): Promise<Note> {
    return request(`/notes/${id}`, { method: "PATCH", body: JSON.stringify(patch) });
  },

  deleteNote(id: number): Promise<void> {
    return request(`/notes/${id}`, { method: "DELETE" });
  },

  shareNote(id: number, userId: number, role: "viewer" | "editor"): Promise<void> {
    return request(`/notes/${id}/shares`, {
      method: "POST",
      body: JSON.stringify({ user_id: userId, role }),
    });
  },
};
