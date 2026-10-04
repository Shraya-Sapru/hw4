// Auth client: talks to the FastAPI /api/auth endpoints and keeps the
// logged-in user's info + session token in localStorage so the login
// persists across page refreshes.
//
// How "staying logged in" works: on signup/login the backend returns a
// JWT (a signed token). We save that token (and a small public profile)
// in localStorage. There's no server-side session to expire on this
// backend yet — the token itself carries an expiry the backend checks
// whenever it's sent back. "Logging out" here just means deleting our
// local copy of the token; nothing needs to happen on the server for a
// stateless token like this.

import { API_BASE_URL } from "./api";

const STORAGE_KEY = "campus_customs_auth";

export interface AuthUser {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
}

interface StoredAuth {
  access_token: string;
  user: AuthUser;
}

type Listener = () => void;
const listeners = new Set<Listener>();

function notify() {
  for (const listener of listeners) listener();
}

export function subscribeAuth(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function readFromLocalStorage(): StoredAuth | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredAuth;
  } catch {
    return null;
  }
}

// Cached in memory so repeated calls return the *same* object reference
// until the auth state actually changes. This matters because
// useSyncExternalStore (used by useAuth) compares snapshots with
// Object.is — if getStoredAuth() parsed localStorage fresh on every
// call, it would return a new object every render and cause an
// infinite re-render loop (which crashes the page blank, since there's
// no error boundary to catch it).
let cachedAuth: StoredAuth | null = readFromLocalStorage();

export function getStoredAuth(): StoredAuth | null {
  return cachedAuth;
}

function setStoredAuth(auth: StoredAuth) {
  cachedAuth = auth;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(auth));
  notify();
}

export function logout() {
  cachedAuth = null;
  localStorage.removeItem(STORAGE_KEY);
  notify();
}

export interface AuthErrorBody {
  detail?: string | { msg: string }[];
}

function extractErrorMessage(body: AuthErrorBody, fallback: string): string {
  if (!body.detail) return fallback;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  return fallback;
}

export async function signup(input: {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(extractErrorMessage(body, "Couldn't create your account."));
  }

  setStoredAuth(body);
}

export async function login(input: { email: string; password: string }): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(extractErrorMessage(body, "Couldn't log you in."));
  }

  setStoredAuth(body);
}
