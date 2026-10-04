import { useSyncExternalStore } from "react";
import { getStoredAuth, subscribeAuth, type AuthUser } from "./auth";

export function useAuth(): { user: AuthUser | null } {
  const stored = useSyncExternalStore(subscribeAuth, getStoredAuth, getStoredAuth);
  return { user: stored?.user ?? null };
}
