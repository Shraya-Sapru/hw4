import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { fetchChatHistory, getBotReply, type ChatMessage } from "../lib/chatClient";
import { imageUrl } from "../lib/api";
import { formatChatText } from "../lib/formatChatText";
import { clearChatSearchState, getChatSearchState, setChatSearchState } from "../lib/chatSearchResults";
import { useAuth } from "../lib/useAuth";
import Mascot from "./Mascot";
import "./ChatWidget.css";

let messageCounter = 0;
function nextId() {
  messageCounter += 1;
  return `msg-${messageCounter}`;
}

const GREETING: ChatMessage = {
  id: "greeting",
  role: "assistant",
  content: "Hi! Ask me anything about Campus Customs gear.",
};

/** Matches /products/<id> so the chat can tell the agent what page the
 * customer is on — lets "do you have this in pink?" resolve without
 * them naming the item. No match on any other page. */
const PRODUCT_PAGE_PATTERN = /^\/products\/([^/]+)$/;

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => [GREETING]);
  const [draft, setDraft] = useState("");
  const [isWaiting, setIsWaiting] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const loadedHistoryForRef = useRef<string | null>(null);

  const pageProductId = PRODUCT_PAGE_PATTERN.exec(location.pathname)?.[1] ?? null;

  // Load the logged-in customer's saved conversation once per login, and
  // clear back to a fresh guest state the moment they log out — or the
  // moment a *different* account logs in directly (e.g. visiting /login
  // again without logging out first). Either way, an old conversationId
  // — and any leftover chat-driven product search results, which can
  // literally say "Hi <previous name>!" in their message text — must
  // never carry over to a new identity.
  useEffect(() => {
    if (loadedHistoryForRef.current === (user?.email ?? null)) return; // no identity change

    const wasLoggedIn = loadedHistoryForRef.current !== null;
    loadedHistoryForRef.current = user?.email ?? null;
    setConversationId(null);
    clearChatSearchState();

    if (user === null) {
      if (wasLoggedIn) setMessages([GREETING]); // logout
      return;
    }

    fetchChatHistory()
      .then((history) => {
        if (history.length === 0) {
          setMessages([GREETING]);
          return;
        }
        setMessages(
          history.map((entry) => ({
            id: nextId(),
            role: entry.role,
            content: entry.content,
          }))
        );
      })
      .catch(() => {
        // No saved history available — not an error worth showing, just
        // start fresh like a guest would.
        setMessages([GREETING]);
      });
  }, [user]);

  // Keep the latest message in view — without this, a reply lands below
  // the fold and has to be scrolled to manually every single time.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, isWaiting]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || isWaiting) return;

    const userMessage: ChatMessage = { id: nextId(), role: "user", content: text };
    setMessages((prev) => [...prev, userMessage]);
    setDraft("");
    setIsWaiting(true);

    try {
      const reply = await getBotReply(text, conversationId, pageProductId);
      setConversationId(reply.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: "assistant",
          content: reply.message,
          products: reply.products.length > 0 ? reply.products : undefined,
        },
      ]);

      // Share the results with the Products page so the matching cards
      // show up there too, not just inline in the chat.
      if (reply.products.length > 0) {
        setChatSearchState({ message: reply.message, products: reply.products });
        navigate("/products");
      } else if (getChatSearchState() !== null) {
        // Already browsing chat-driven results and this follow-up came
        // back empty — reflect that (rather than leaving the old cards
        // up looking current) instead of silently doing nothing.
        setChatSearchState({ message: reply.message, products: [] });
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: "assistant",
          content: "Sorry, I couldn't reach the shop assistant just now. Please try again in a moment.",
        },
      ]);
    } finally {
      setIsWaiting(false);
      inputRef.current?.focus();
    }
  }

  return (
    <div className="chat-widget">
      {isOpen && (
        <div className="chat-widget__panel" role="dialog" aria-label="Campus Customs chat">
          <div className="chat-widget__header">
            <span className="chat-widget__header-title">
              <Mascot size={24} bounce={false} wave={false} />
              Campus Customs Chat
            </span>
            <button
              type="button"
              className="chat-widget__close"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          <div className="chat-widget__messages">
            {messages.map((message) => (
              <div key={message.id} className={`chat-widget__row chat-widget__row--${message.role}`}>
                {message.role === "assistant" && (
                  <div className="chat-widget__avatar">
                    <Mascot size={28} bounce={false} wave={false} />
                  </div>
                )}
                <div className={`chat-widget__bubble chat-widget__bubble--${message.role}`}>
                  {message.role === "assistant" ? formatChatText(message.content) : message.content}
                  {message.products && message.products.length > 0 && (
                    <div className="chat-widget__products">
                      {message.products.map((product) => (
                        <Link
                          key={product.product_id}
                          to={`/products/${product.product_id}`}
                          className="chat-widget__product-card"
                          onClick={() => setIsOpen(false)}
                        >
                          <img src={imageUrl(product.image_url)} alt={product.name} />
                          <div>
                            <p className="chat-widget__product-name">{product.name}</p>
                            <p className="chat-widget__product-price">
                              ${product.price.toFixed(2)}
                            </p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isWaiting && (
              <div className="chat-widget__row chat-widget__row--assistant">
                <div className="chat-widget__avatar">
                  <Mascot size={28} bounce={false} wave={false} />
                </div>
                <div
                  className="chat-widget__bubble chat-widget__bubble--assistant chat-widget__typing"
                  aria-label="Assistant is typing"
                >
                  <span className="chat-widget__typing-dot" />
                  <span className="chat-widget__typing-dot" />
                  <span className="chat-widget__typing-dot" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form className="chat-widget__form" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Type a message…"
              aria-label="Chat message"
            />
            <button type="submit" disabled={!draft.trim() || isWaiting}>
              Send
            </button>
          </form>
        </div>
      )}

      <button
        type="button"
        className="chat-widget__toggle"
        onClick={() => setIsOpen((open) => !open)}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? "×" : <Mascot size={36} bounce={false} wave={false} />}
      </button>
    </div>
  );
}
