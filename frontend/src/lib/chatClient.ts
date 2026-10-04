// Chat client for the floating chat widget.
//
// Calls the FastAPI backend's PydanticAI-powered /api/chat endpoint and
// returns its reply (text plus optional product cards). The backend
// keeps each conversation's message history server-side, keyed by
// conversation_id — pass back the id from the previous reply so the
// agent remembers earlier turns (e.g. which product was being
// discussed); leave it unset to start a fresh conversation.
//
// When logged in, the stored session token is sent as an Authorization
// header so the backend knows who's asking (never anything we send in
// the message body itself) — that's what lets the agent greet the
// customer by name and save/reload their chat history.

import { API_BASE_URL } from "./api";
import { getStoredAuth } from "./auth";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  products?: ChatProductCard[];
}

export interface ChatProductCard {
  product_id: string;
  name: string;
  price: number;
  image_url: string;
  description: string;
}

export interface BotReply {
  message: string;
  products: ChatProductCard[];
  conversation_id: string;
}

export interface ChatHistoryEntry {
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

function authHeaders(): Record<string, string> {
  const stored = getStoredAuth();
  return stored ? { Authorization: `Bearer ${stored.access_token}` } : {};
}

export async function getBotReply(
  userMessage: string,
  conversationId: string | null,
  pageProductId: string | null
): Promise<BotReply> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({
      message: userMessage,
      conversation_id: conversationId,
      page_product_id: pageProductId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat request failed (${response.status})`);
  }

  return response.json();
}

/** Only call this when logged in — a guest has nothing saved to fetch. */
export async function fetchChatHistory(): Promise<ChatHistoryEntry[]> {
  const response = await fetch(`${API_BASE_URL}/api/chat/history`, {
    headers: authHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to load chat history (${response.status})`);
  }

  return response.json();
}
