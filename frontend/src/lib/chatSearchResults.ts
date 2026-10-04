// Shared "chat-driven product search" state.
//
// The chat widget lives on every page (it's rendered once, outside
// <Routes>, in App.tsx), but the Products page is a sibling, not a
// parent/child of it — so when the chatbot finds matching products, the
// only way for the Products page to show them is through state that
// lives outside both components. This is that shared state.
//
// Follows the same pattern as lib/auth.ts: a module-level value, a
// subscribe/notify pair for React to hook into via useSyncExternalStore,
// and — importantly — the getter always returns the *same* object
// reference until something actually calls set/clear. (Building a new
// object on every read broke the Navbar's login state earlier in this
// project with an infinite re-render loop; same fix applies here.)

import type { ChatProductCard } from "./chatClient";

export interface ChatSearchState {
  message: string;
  products: ChatProductCard[];
}

type Listener = () => void;
const listeners = new Set<Listener>();

function notify() {
  for (const listener of listeners) listener();
}

export function subscribeChatSearch(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

let current: ChatSearchState | null = null;

export function getChatSearchState(): ChatSearchState | null {
  return current;
}

export function setChatSearchState(state: ChatSearchState) {
  current = state;
  notify();
}

export function clearChatSearchState() {
  current = null;
  notify();
}
