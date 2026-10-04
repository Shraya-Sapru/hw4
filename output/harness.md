# Database Analysis — data/campus_customs.db

Read-only analysis of the SQLite database at `data/campus_customs.db`. No writes were made.

The database has 5 tables: `catalogue`, `inventory`, `users`, `chat_messages`, and `sqlite_sequence`
(an internal SQLite bookkeeping table that tracks autoincrement counters — not app data, skipped below).

---

## catalogue (102 rows)

One row per product.

| Field | Why it's useful |
|---|---|
| `product_id` | Stable key used to link a product to its `inventory` rows and to any product the chatbot references in `chat_messages.products_json`. |
| `name` | Human-readable product name to show in search results, the product panel, and chatbot replies. |
| `garment_type` | Lets the chatbot/website filter or group products by type (e.g. "show me hoodies"). |
| `description` | Gives the chatbot detail to describe a product in a reply, or to match against descriptive questions ("what colors does this come in"). |
| `colors` | JSON list of colors — lets the chatbot answer "do you have this in pink?"-style questions by checking available colors. |
| `search_tags` | JSON list of keywords (sport, style, team, etc.) — powers keyword/semantic search so the chatbot can match loose natural-language queries to products. |
| `image_file_path` | Relative path to the product's image under `data/products/`, used to render the product photo on the site. |
| `price` | Needed to answer price questions and to display/sum totals for the shop. |

**Sample rows:**
```
product_id: 2025-yale-vs-harvard-t-shirt
name: 2025 Yale Vs Harvard T Shirt
garment_type: short-sleeve T-shirt
description: Heather gray short-sleeve T-shirt featuring a 2025 Harvard-Yale The Game graphic, with red Harvard and navy Yale football helmets facing each other and collegiate team marks.
colors: ["heather gray", "white", "red", "navy blue"]
search_tags: ["Yale", "Harvard", "The Game", "2025", "Harvard Yale football", "college rivalry", "football helmet graphic", "gray T-shirt", "Campus Customs"]
image_file_path: products/2025-yale-vs-harvard-t-shirt.jpg
price: 32.0

product_id: baseball-left-chest-crewneck
name: Baseball Left Chest Crewneck
garment_type: crewneck sweatshirt
description: Navy long-sleeve crewneck sweatshirt with ribbed collar, cuffs, and waistband, featuring a white YALE BASEBALL wordmark on the left chest.
colors: ["navy", "white"]
search_tags: ["Yale", "baseball", "crewneck", "sweatshirt", "navy sweatshirt", "left chest logo", "long sleeve", "college merch"]
image_file_path: products/baseball-left-chest-crewneck.jpg
price: 58.0
```

---

## inventory (612 rows)

One row per (product, size) combination — stock levels.

| Field | Why it's useful |
|---|---|
| `id` | Auto-incrementing row key, not meaningful to the shop logic itself. |
| `product_id` | Foreign key back to `catalogue.product_id`, so stock can be joined onto a product. |
| `size` | Needed to answer "what sizes are available" and to let a customer pick a size. |
| `quantity` | Needed to answer stock/availability questions ("is this in stock in Medium?") and to prevent selling out-of-stock sizes. |

**Sample rows:**
```
id: 1, product_id: 2025-yale-vs-harvard-t-shirt, size: XS, quantity: 25
id: 2, product_id: 2025-yale-vs-harvard-t-shirt, size: S,  quantity: 25
id: 3, product_id: 2025-yale-vs-harvard-t-shirt, size: M,  quantity: 20
```

---

## users (3 seed rows as of this analysis; grows as people sign up)

Registered shopper accounts. Password hashes are intentionally left out of this file.

The 3 rows below are the original seed data this analysis was written against (Problem 2).
Since then, real signups have added more rows through `/api/signup` — this table is live and
will keep growing, so don't expect the row count or sample rows here to stay in sync with the
actual database.

| Field | Why it's useful |
|---|---|
| `id` | Primary key, links a user to their own `chat_messages` rows (own conversation history). |
| `name` | Full display name shown in the UI. |
| `email` | Login identifier; also useful for account-specific messages (order confirmations, etc.). |
| `password_hash` | *(omitted from this file — needed only for login verification, never shown back to a user.)* |
| `created_at` | Account creation timestamp, useful for admin/analytics views. |
| `first_name` / `last_name` | Split name fields, handy for personalized greetings in the chatbot ("Hi Ada, ..."). |

**Sample rows (password_hash omitted):**
```
id: 1, name: Test User,     email: test@campuscustoms.yale.edu, created_at: 2026-09-19 11:34:09, first_name: Test,   last_name: User
id: 2, name: Ada Lovelace,  email: ada.1789818990@yale.edu,     created_at: 2026-09-19 11:56:30, first_name: Ada,    last_name: Lovelace
id: 3, name: Tauhid Zaman,  email: tauhid.zaman@yale.edu,       created_at: 2026-09-19 11:57:56, first_name: Tauhid, last_name: Zaman
```

---

## chat_messages (22 rows)

Log of chatbot conversation turns, one row per message.

| Field | Why it's useful |
|---|---|
| `id` | Primary key, also gives message ordering. |
| `user_id` | Foreign key to `users.id` — keeps each shopper's conversation history separate. |
| `role` | Either `"user"` or `"assistant"` — needed to reconstruct the back-and-forth conversation and to feed prior turns back into the model as context. |
| `content` | The actual message text shown in the chat window. |
| `products_json` | JSON list of full product records (with inventory) the assistant decided were relevant to its reply — lets the website render a matching product panel alongside the chat answer, and shows exactly what data the model was grounded on. |
| `created_at` | Timestamp, used for ordering and showing message times in the UI. |

**Sample rows (products_json shown trimmed to first product only, for readability):**
```
id: 1, user_id: 1, role: user, created_at: 2026-09-19 11:40:23
content: "What hoodies do you have?"
products_json: null

id: 2, user_id: 1, role: assistant, created_at: 2026-09-19 11:40:23
content: "We carry these hoodies, all priced at **$68**: Basic Hoodie Big Yale, Champion Reverse Weave Hoodie, Crew Left Chest Hoodie, Vintage Bulldog Hoodie, Vintage Sailor Bulldog Hoodie, Fencing Left Chest Hoodie, Ice Hockey Left Chest Hoodie, Sailing Left Chest Hoodie. They're now displayed on the product panel. Sizes and availability vary by style."
products_json (first entry only): [{"product_id": "basic-hoodie-big-yale", "name": "Basic Hoodie Big Yale", "garment_type": "pullover hoodie", "price": 68.0, "inventory": [{"size": "XS", "quantity": 15}, {"size": "S", "quantity": 5}, ...], "total_stock": 60}, ... 7 more products ...]

id: 3, user_id: 1, role: user, created_at: 2026-09-19 11:52:33
content: "you have this in pink?"
products_json: null
```

---

# Authentication — how sign up and log in work

Implemented in `backend/security.py`, `backend/session.py`, and `backend/auth.py`.
No real hashes, tokens, or secret values appear below — just the mechanism.

## Which `users` fields this uses

| Field | Role in authentication |
|---|---|
| `email` | The login identifier. Stored and compared case-insensitively (`lower(email)`), so `Ada@yale.edu` and `ada@yale.edu` are the same account. Has a `UNIQUE` constraint in the schema, which backs up our own duplicate-email check. |
| `password_hash` | Never the plain password — see hashing below. Only ever read (to verify a login) or written once (at signup). It is never sent back to the frontend in any response. |
| `first_name`, `last_name` | Collected at signup, returned in the login/signup response so the frontend can show "Hi, \<name\>" without a second request. |
| `name` | Kept in sync as `"<first_name> <last_name>"` for consistency with how the three seed accounts were stored, but it isn't used for login. |
| `id`, `created_at` | `id` is embedded in the session token (see below) so later requests can be tied back to a user; `created_at` is just a timestamp, not used by auth logic. |

## How passwords are hashed

Passwords are never stored or logged in plain text. We hash with **PBKDF2-HMAC-SHA256**,
the same algorithm family the three seed accounts (Test User, Ada Lovelace, Tauhid Zaman)
were already using — their `password_hash` values are a `$`-joined string:

```
pbkdf2_sha256$<salt>$<hex digest>
```

For every new signup, we:
1. Generate a random salt.
2. Run PBKDF2-HMAC-SHA256 over the password + that salt for a fixed number of iterations
   (a constant in `security.py`).
3. Store `pbkdf2_sha256$<salt>$<digest>` — never the password itself.

**On the iteration count:** it isn't recorded anywhere in the hash string itself, so it
couldn't be read off directly from the seed data. It was confirmed instead by testing the
known `test@campuscustoms.yale.edu` seed login against a range of common iteration counts
until one reproduced that account's exact stored hash. That confirmed value is what
`security.py` now uses for every password this app hashes or verifies, so it matches
whatever originally seeded the `users` table. The other two seed accounts (Ada Lovelace,
Tauhid Zaman) are assumed to share the same iteration count since they use the same hash
format, but their actual passwords were never tested or confirmed.

## How login is verified

1. Look up the row where `lower(email)` matches the submitted email.
2. If no row is found, **or** if the password re-hashed with that row's stored salt and our
   iteration count doesn't match the stored digest, return the exact same generic error:
   *"Incorrect email or password."* Using one identical message for both cases means a caller
   can't use the login endpoint to probe which emails have accounts.
3. Hash comparison is constant-time (not a plain `==`), so a mismatch can't be timed to leak
   how much of the digest happened to match.

## Login lockout (rate limiting)

Implemented in `backend/rate_limit.py`, used by the login endpoint only.

After **5 failed login attempts in a row for the same email**, further attempts for that email
are rejected immediately with a 429 and a "try again in about N minute(s)" message, for 5
minutes — without even checking the database, so a locked-out account can't be used to keep
guessing passwords during the lockout window. A successful login clears the count back to zero,
so one correct login undoes any prior failed attempts.

This is **in-memory, not a database table** — the project's rule is that this backend only ever
writes to `users`, and a failed-attempt counter is transient rate-limit bookkeeping, not account
data. The trade-off: the counters reset if the backend process restarts, and wouldn't be shared
if this were ever run as multiple server processes at once. For this project (one local dev
server) that's a reasonable trade-off; a production deployment with multiple instances would
want this in something shared, like Redis, instead.

## How the session is handled

There's no `sessions` table — the task only allows writes to `users`, and a stateless approach
doesn't need one. Instead, a successful signup or login returns a **JWT** (a signed token):

- The token's contents include the user's id, email, and an expiry time.
- It's signed with a secret key (`SESSION_SECRET_KEY`) that lives only in the project's
  `.env` file — never in this repo, never sent to the frontend.
- Because it's signed, the backend can later confirm a token is genuine and unexpired without
  looking anything up in a database — the token proves itself.
- The frontend stores the token (in `localStorage`, alongside the user's public profile) and
  would send it back as `Authorization: Bearer <token>` on any future request that needs to
  know who's logged in.
- "Logging out" is purely a frontend action — deleting the locally stored token. There's
  nothing server-side to invalidate for a token like this, since the server never stored it
  in the first place.

---

# The chatbot — how the frontend talks to FastAPI, and how the agent is built

## The route

`POST /api/chat`, defined in `backend/main.py`.

**Request body** (`ChatRequest` in `backend/models.py`):
```json
{ "message": "What hoodies do you have?", "conversation_id": null }
```
`conversation_id` is `null` (or omitted) to start a new conversation. To continue one, send
back the `conversation_id` from the previous reply — this is how the agent remembers earlier
turns (e.g. which product was being discussed), instead of treating every message as a brand
new conversation with no memory of anything said before.

**Response body** (`ChatResponse` in `backend/models.py`):
```json
{
  "message": "...the assistant's reply...",
  "products": [],
  "conversation_id": "ddc08e6e973b4f5db352bac5dfc367a8"
}
```
`products` is **always a list, never null** — an empty list covers both "this wasn't a product
question" and "it was, but nothing matched," so the frontend never has to branch on null vs.
empty. When it's non-empty, each entry is a `ProductCard` (`product_id`, `name`, `price`,
`image_url`, `description`) that genuinely came back from a tool call — `search_products` for a
category/keyword browse, or the specific item a price/stock question was about. The system
prompt is explicit that the agent must never put anything in `products` that a tool didn't
actually return.

Note that `ChatResponse` (the actual HTTP response) is a different type from `ChatReply` (the
agent's own structured output type): the agent only ever fills in `message` and `products` — it
has no business generating a `conversation_id` itself, so that's added on top, server-side, once
the agent has finished.

The floating chat widget (`frontend/src/components/ChatWidget.tsx`) calls this route through
`frontend/src/lib/chatClient.ts`'s `getBotReply()`. It keeps the `conversation_id` in React state
and sends it on every message after the first, shows `message` as the assistant's chat bubble,
and renders a small product card under that bubble for each entry in `products`, if any.

## Conversation memory

Implemented in `backend/conversations.py`, used by `run_agent()` in `backend/agent.py`.

Each conversation's message history (in PydanticAI's own message format, via
`result.all_messages()`) is kept in an in-memory dict keyed by `conversation_id`. On each
request: look up that conversation's prior history (empty list if it's a new conversation),
pass it to `agent.run(message, message_history=history)`, then save the updated history back
under the same id for next time.

Like the login lockout counters in `rate_limit.py`, this is deliberately in-memory rather than
a database table — it's transient session state, not account data, and the backend only ever
writes to `users`. Same trade-off as that: conversation memory resets if the backend restarts,
and wouldn't be shared across multiple server processes — fine for a single local dev server.

## How the agent gets loaded

`backend/agent.py` builds the agent once, when the backend starts:

1. **System prompt** — read from `backend/prompts/prompt.md` as a plain text file at startup.
   Editing that file and restarting the backend is enough to change the agent's instructions;
   nothing in `agent.py` needs to change.
2. **Model + routing** — the agent talks to an OpenAI-compatible model (`gpt-5.6-terra`) through
   an `AsyncOpenAI` client whose `base_url` points at Portkey rather than OpenAI directly, with
   the real provider named via a `x-portkey-provider` header. Portkey then routes the request to
   the actual model.
3. **API key** — read from `PORTKEY_API_KEY` in the project's root `.env` file (two folders up
   from `backend/`) via `python-dotenv`. It's never hardcoded, never logged, and never part of
   any response.
4. **Structured output** — the agent's `output_type` is `ChatReply` itself (not plain text), so
   the model's reply is directly validated into a `{message, products}` shape — there's no
   separate "wrap the text in JSON" step. `run_agent()` then adds `conversation_id` on top to
   build the `ChatResponse` that `/api/chat` actually returns (see "Conversation memory" above).
5. **Tools** — passed in from `backend/tools.py`: `search_products`, `get_product_details`, and
   `check_stock`, all read-only lookups against the real catalogue/inventory data (see "Agent
   tools" below).
6. **Failure handling** — if the model call itself fails (a content filter rejection, a rate
   limit, a network blip), `run_agent()` catches that and returns a friendly fallback message
   instead of letting the request crash with a 500.

Running the backend: `cd backend`, then `python -m uvicorn main:app --port 8000` (using the
project's `.venv` interpreter). All of this — the database, `data/products/`, the root `.env`,
and `prompts/prompt.md` — is located by each module using its own file path (`Path(__file__)`),
so it all resolves correctly regardless of which folder the command is actually run from.

---

# Agent tools — real catalogue lookups

Implemented in `backend/tools.py`, all read-only (SQLite's `mode=ro` URI) with parameterized
`?` queries, same guarantees as the rest of the backend. Registered with the agent in
`backend/agent.py` via `tools=TOOLS`. `prompts/prompt.md` now tells the agent to always use
these for price, description, or stock questions, rather than answering from memory.

## search_products(query)

Searches the catalogue by name, description, garment type, or search tags. The query is split
into individual words, and every word has to appear *somewhere* in a product's combined
searchable text — not necessarily the same column, and not necessarily adjacent or in order.
That's deliberate: a query like "forest hoodie" still finds "The Forest School Hoodie" even
though "School" sits between those two words in the real name — requiring the whole query as
one literal contiguous phrase was the original (buggy) behavior, and it missed real matches
whenever someone phrased things even slightly differently than the catalogue text. Use this
when someone describes what they want in words rather than naming an exact product. Capped at
8 results.

Matching is **whole-word**, via a SQLite `REGEXP` operator backed by a small Python function
registered on each connection (`\b<word>\b`, with hyphens stripped from both the query word and
the column text first, so "tshirt" / "t-shirt" / "t shirt" all line up the same way). This
replaced an earlier version that used plain `LIKE '%word%'` substring matching, which had a real
bug: "tshirt" is a literal substring of "sweatshirt" (swea-**tshirt**), so searching for T-shirts
incorrectly returned crewneck sweatshirts instead — while also *failing* to match real,
hyphenated "t-shirt" catalogue entries at all, since the hyphen broke the plain substring check.
Whole-word matching on hyphen-normalized text fixes both problems at once.

**Returns `ProductSearchResult`:**

| Field | Why it's there |
|---|---|
| `query` | Echoes back what was searched, so the agent (and anyone debugging) can see what the tool was actually asked. |
| `found` | Explicit yes/no for "did anything match" — the agent can check this directly instead of inferring "nothing found" from an empty list, which is one less thing it could get wrong. |
| `matches` | A list of `ProductCard`s (not just IDs) — the agent can describe multiple options *and* attach them as product cards in the same reply, which is what powers the "which one do you mean?" behavior. |

## get_product_details(product_id)

Looks up one product's full description, price, and colors by its exact `product_id`.

**Returns `ProductLookupResult`:**

| Field | Why it's there |
|---|---|
| `found` | Lets the agent tell "this product doesn't exist" apart from "it exists but I have nothing to say" — both would otherwise look like an empty response. |
| `product` | `None` when not found, otherwise a `ProductDetails` with `product_id`, `name`, `garment_type`, `description`, `price`, `colors`, and `image_url` — everything needed to both answer in words and attach a product card. |

## check_stock(product_id, size=None)

Checks stock for one product — either a specific size, or every size at once if `size` is left
unset. Size matching is case-insensitive (`'m'` matches `'M'`).

**Returns `StockCheckResult`:**

| Field | Why it's there |
|---|---|
| `product_found` | Same reasoning as `found` above — tells apart "no such product" from "product exists, no stock data." |
| `product_id` / `size_requested` | Echoed back, so the agent (and logs) can see exactly what was asked, even for a multi-size result. |
| `sizes` | A list of `StockLevel` (see below). Can be empty two different ways — see the note below. |

**`StockLevel` fields, and why both `quantity` and `in_stock` exist:** `quantity` is the real
number, for when someone asks "how many are left." `in_stock` is a plain boolean the agent can
act on directly to say "that's out of stock" — without it, the agent would have to do its own
`quantity > 0` comparison in its head, which is exactly the kind of small reasoning step where a
model can slip up. Giving it the boolean directly removes that risk.

**The two different meanings of an empty `sizes` list** — this is the part worth being precise
about, since it's easy to conflate:
- **`product_found=False`**: the product itself doesn't exist at all.
- **`product_found=True`, a `size_requested` was given, `sizes` is still empty**: the product
  exists, but isn't offered in that size (e.g. asking for a "4XL" that was never a SKU for this
  item). This is different from being *out of stock* in that size — that case instead returns
  exactly one `StockLevel` with `quantity=0, in_stock=False`.

## suggest_alternatives(product_id=None)

Added in Problem 9. Finds real alternatives when `check_stock` shows something unavailable —
used right after an out-of-stock answer, not on its own. Same `product_id`-falls-back-to-page-context
and `ModelRetry`-if-neither pattern as `get_product_details`/`check_stock`.

**Returns `AlternativesResult`:**

| Field | Why it's there |
|---|---|
| `product_found` | Same reasoning as elsewhere — "no such product" vs. "product exists." |
| `other_in_stock_sizes` | Other sizes of this *same* product that are actually in stock right now (a plain query: same `product_id`, `quantity > 0`). Empty if every other size is also out. |
| `similar_in_stock_products` | Other products sharing this one's `garment_type`, excluding itself, with at least one size in stock (an inventory join, capped at 5 results). Empty if nothing else of that type has any stock. |

Both lists being empty is a real, valid answer — "we don't have an alternative" — not a failure;
the agent is told to say so rather than inventing something to offer.

---

# How chat search results reach the page

The chatbot can make the Products page itself show matching products — not just list them
inside the chat bubble — even though the chat widget is rendered once, on every page, as a
sibling of whatever page is currently showing (not a parent of it).

## The flow, end to end

1. **Agent finds matches** — a category/keyword question ("show me hoodies") makes the agent
   call `search_products` and put every real match into `ChatReply.products`, per the system
   prompt rule.
2. **`/api/chat` returns them** — as a `ChatResponse` with a `products` list (see "The route"
   above). Each entry carries `product_id`, `name`, `price`, `image_url`, `description` — enough
   to render a card and to link to that product's own detail page.
3. **The chat widget receives the reply** (`frontend/src/components/ChatWidget.tsx`) and, if
   `products` is non-empty:
   - shows them as small cards right in the chat bubble (immediate feedback in the conversation), and
   - calls `setChatSearchState({ message, products })` from `frontend/src/lib/chatSearchResults.ts`,
     and navigates to `/products`.
4. **`chatSearchResults.ts` is the shared store** that makes step 3 visible outside the chat
   widget. It's a small module-level store (same pattern as `lib/auth.ts`): a value, a
   subscribe/notify pair, and a React hook (`useChatSearch`, via `useSyncExternalStore`) that any
   component can read. This is necessary specifically because the chat widget and the Products
   page are siblings in the component tree (the chat widget sits outside `<Routes>` in `App.tsx`
   so it appears on every page) — there's no parent/child relationship to pass the data through
   directly, so it has to live somewhere both can reach.
5. **The Products page reads that shared state** (`frontend/src/pages/Products.tsx`). If a chat
   search is active, it renders those products instead of fetching the full catalogue — using
   the exact same `CatalogueCard` component the normal "All Products" view uses, so the cards
   look identical either way. If the chat search came back with zero matches, it shows a
   friendly "No matching products found" message instead of an empty grid.
6. **"Show all products"** — a button on the Products page calls `clearChatSearchState()`,
   which wipes the shared state and makes the page fall back to its normal full-catalogue fetch.

## Why `CatalogueCard` didn't need to change

The chatbot's `ProductCard` (from `/api/chat`) and the catalogue's `ProductSummary` (from
`/api/products`) are two different backend types, but they overlap in exactly the fields a card
actually needs to render. `frontend/src/lib/api.ts` defines a `DisplayProduct` interface with
just that overlap (`product_id`, `name`, `price`, `image_url`, `description`), and
`CatalogueCard` was narrowed to accept that instead of `ProductSummary` specifically — both real
types satisfy it structurally, so the same card component, and the same `Link`, works for both
without needing two near-identical components.

## How clicking a card reaches the detail page

Every card — the ones in the chat bubble and the ones on the Products page — is a React Router
`Link` to `/products/<product_id>`, using the exact `product_id` the backend returned. That
route renders `ProductDetail.tsx`, which fetches `/api/products/<product_id>` itself — the same
full detail endpoint the regular Products page cards use, returning the large image, full
description, price, colors, and the complete sizes/stock table. Chat-driven cards and
catalogue-page cards land on the literal same page component with the literal same data; there's
no separate "chat version" of the detail page to keep in sync.

---

# Customer memory — saved chat history, who the agent can see, and page context

## Where chat history is stored

Reuses the `chat_messages` table that was already in the seed database (`user_id`, `role`,
`content`, `products_json`, `created_at`) — it already had exactly this shape, so no new table
or schema change was needed. `backend/chat_history.py` is the only code that touches it:
`save_message()` (one parameterized INSERT) and `get_recent_history()` (one parameterized
SELECT, most recent rows, returned oldest-first). Only ever reads/writes this one table — never
`users` or anything else.

**Only logged-in customers get saved**, and the decision is made server-side, not trusted from
the frontend: `run_agent()` only calls `save_message()` when a real `AuthenticatedUser` came
back from `get_current_user()` (see below). A guest's conversation still works turn-to-turn
(the existing in-memory `conversations.py` store from Problem 6/7 handles that), but nothing
from it is ever written to the database, and it's gone once the in-memory store expires or the
backend restarts.

**Continuing across visits:** when a logged-in customer starts a brand-new conversation (no
`conversation_id` yet), `_history_messages_to_seed()` loads their recent saved messages and
turns them into PydanticAI message history before the first run — so they can pick up an
earlier conversation, not just the current browser session.

## Who's making the request — never trusted from the message itself

`backend/auth.py`'s `get_current_user()` is a FastAPI dependency used by both `/api/chat` and
`/api/chat/history`. It reads the `Authorization: Bearer <token>` header, decodes the session
JWT (from Problem 4), and looks up that user's row by the id *inside the token* — nothing about
who's asking ever comes from the request body. An invalid, missing, or expired token quietly
resolves to `None` (a guest) rather than erroring, since chat has to keep working for guests too.

(Fixed along the way: PyJWT enforces that the `sub` claim must be a string per the JWT spec, but
the original Problem 4 token-creation code put the raw integer user id there. This had been
silently unused ever since — nothing before Problem 8 ever actually decoded a token — so the bug
was invisible until `get_current_user` became the first real caller of `decode_session_token`.
Fixed by stringifying `sub` on encode and parsing it back to `int` on decode.)

## What the agent can see about the customer

Deliberately narrow, defined in `backend/deps.py`'s `ChatDeps` and `backend/models.py`'s
`CustomerInfo`:

| Field | Source |
|---|---|
| `first_name`, `last_name`, `email` | The logged-in customer's own row, nothing else |

That's it — no password hash, no user id, no other customer's data, ever. `ChatDeps.user` is
`None` entirely for a guest, and the system prompt (`backend/agent.py`'s `customer_context()`,
registered as a dynamic system prompt via `@agent.system_prompt`) explicitly tells the model
whether it's talking to a named customer or a guest, so it can greet someone by name without the
prompt text itself needing to change.

**A real bug found while wiring this up:** PydanticAI only generates system-prompt messages
when the `message_history` passed to `agent.run()` is completely empty — it assumes a non-empty
history already has them from an earlier real run through this same agent. That's true for
in-memory continuing conversations (they really did come from a prior `agent.run()` call), but
the seeded-from-database history built for a returning logged-in customer is synthetic — it
never went through a real run, so it had no system-prompt parts at all. Without a fix, every
guardrail and all customer/page context would have silently vanished the moment a returning
customer's history was loaded. Fixed by rendering the same static + dynamic system prompt
content by hand and prepending it to that seeded history, exactly mirroring what a real first
turn would have produced.

## Page context — what "this" means

`ChatRequest.page_product_id` (frontend sends it; `None` on any page that isn't a product page)
becomes `ChatDeps.product_context_id`. The frontend (`ChatWidget.tsx`) derives it by matching
the current route against `/products/<id>` — it doesn't need any special wiring from the
product page itself, since the chat widget can read the URL directly.

Both `get_product_details` and `check_stock` in `tools.py` take `product_id` as *optional* now:
if the model doesn't name one explicitly, the tool falls back to `ctx.deps.product_context_id`.
If there's no name **and** no page context, the tool raises `ModelRetry` with a message telling
the model to ask which item the customer means — rather than the model having to realize on its
own that it's missing information, the tool itself enforces that rule deterministically every
time.

## The frontend side

- **Loading history:** `ChatWidget.tsx` watches the logged-in user (via `useAuth()`) and, the
  first time it sees one, calls `GET /api/chat/history` and replaces the canned greeting with
  their real past messages. This happens as soon as the user is known (not gated on the panel
  being opened), so there's no visible loading delay the moment they actually open the chat.
- **Guests** just get the canned greeting, unchanged from before.
- **Logging out, or switching directly to a different account** (e.g. visiting `/login` again
  without logging out first) is detected the same way — any change in *who's* logged in, not
  just the specific case of becoming a guest — and resets the widget to the canned greeting with
  a fresh `conversation_id`, so neither a stale conversation nor someone else's messages ever
  carry over to the next identity using that browser tab.
- **Auto-scroll:** a sentinel `<div>` after the last message, scrolled into view with
  `scrollIntoView({ behavior: "smooth" })` whenever `messages` or the "Thinking…" state changes —
  this is also the fix for the "I have to scroll down myself to see each reply" issue.

## Verified example — a real logged-in conversation

Captured from an actual session (not a scripted test), as evidence the pieces above genuinely
work together rather than just in isolation:

> **You:** What hoodies do you have?
> **Assistant:** We carry these hoodies, all priced at **$68**: Basic Hoodie Big Yale, Champion
> Reverse Weave Hoodie, Crew Left Chest Hoodie, Vintage Bulldog Hoodie, Vintage Sailor Bulldog
> Hoodie, Fencing Left Chest Hoodie, Ice Hockey Left Chest Hoodie, Sailing Left Chest Hoodie.
> They're now displayed on the product panel. Sizes and availability vary by style.
>
> **You:** you have this in pink?
> **Assistant:** No — this Baseball Left Chest Crewneck is only available in navy and white, not
> pink. It's $58 and currently in stock in sizes S, M, L, and XXL.
>
> **You:** Hi — do you remember me? What's my name?
> **Assistant:** Hi, Test! I can see you're logged in as **Test User**. Welcome back!
>
> **You:** Hi can you tell me what tshirt options we have
> **Assistant:** Hi Test! Here are our current T-shirt options — each is $32: ...
>
> **You:** is L available
> **Assistant:** For the T-shirts we just reviewed, size L is available in: 2025 Yale Vs Harvard
> T Shirt — 2 left, Benjamin Franklin T Shirt — 25 left, District Tri Blend T Shirt Vintage
> Shield — 8 left, Football Left Chest T Shirt — 2 left, Grace Hopper Logo T Shirt — 8 left,
> Morse Logo T Shirt — 12 left. Size L is out of stock in the Big Yale Tri Blend T Shirt and
> Boola Boola T Shirt.
>
> **You:** what is my name and email id
> **Assistant:** Your name is **Test User**, and the email on your account is
> **test@campuscustoms.yale.edu**.

What this actually demonstrates, turn by turn: real category search (hoodie list), grounded
color reasoning on a specific product without being told which one, genuine name recall for a
logged-in customer, and — notably on the "is L available" turn — real conversation memory: the
agent correctly resolved "L" and "the T-shirts we just reviewed" back to the *six* T-shirts from
two turns earlier and checked real stock for every one of them, rather than needing the
customer to repeat or name anything.

---

# `GET /api/chat/history` — the one remaining `models.py` type

The last `models.py` type not already covered above: `ChatHistoryMessage`, the shape returned by
this endpoint (used by the frontend on login to restore a returning customer's chat panel — see
"The frontend side" above).

| Field | Why it's there |
|---|---|
| `role` | `"user"` or `"assistant"` — lets the frontend render each bubble on the correct side. |
| `content` | The message text itself. |
| `created_at` | Lets the frontend order messages and, if it ever wants to, show a timestamp. |

This intentionally mirrors `chat_messages.role`/`content`/`created_at` directly — it's a thin,
read-only view over that table (via `get_recent_history()`), not a separate shape with its own
reasoning.

---

# Audit trail, safety limits, and the safety prompt (Problem 12)

## Why an audit trail, and what it's for

Every tool call the agent makes, and the outcome of every `/api/chat` run, is appended to
`output/audit_trail.json` by `backend/audit.py`. The point is a record an instructor (or a
developer debugging a weird conversation) can read afterward to see exactly what the agent did
and why a run ended the way it did — without that record ever being able to leak a password, a
hash, an API key, or long raw message text, and without a concurrent request or a server restart
ever being able to corrupt or erase it.

## Entry shape

Two kinds of entry, sharing one shape:

| Field | Meaning |
|---|---|
| `timestamp` | UTC, ISO-8601, when the entry was written. |
| `conversation_id` | Correlates every entry — tool calls and the final run summary — from the same `/api/chat` run. |
| `event` | `"tool_call"` or `"run_summary"`. |
| `tool_name` | Which tool ran, for a `tool_call` entry; `null` for a `run_summary`. |
| `summary` | For a `tool_call`: `{args, result}`, both passed through `summarize_value()` (see below). For a `run_summary`: `{requests, tool_calls}`, the real counts from that run's `result.usage`, or both `null` if the run never got that far (e.g. it was rejected before the model was even called). |
| `stop_reason` | `null` on a `tool_call` entry. On a `run_summary`: `"completed"`, `"usage_limit_exceeded"`, `"message_too_long"`, or `"model_error"` (see "Stop reasons" below). |

## How entries stay safe to read

`summarize_value()` (in `audit.py`) runs over every `args`/`result` value before it's ever
written:
- Any string longer than 60 characters is truncated with a trailing `…` — long free-text (a
  product description, a customer's actual message) never appears in full.
- Any list longer than 3 items is cut down to 3, with a `"…(+N more)"` marker — a search result
  with 8 matches doesn't balloon the log.
- Any dict key whose name contains `password`, `hash`, `token`, `key`, `secret`, or
  `authorization` (case-insensitive) is replaced with `"«redacted»"` outright, recursively, at
  any nesting depth — defense in depth, even though none of the four tools' actual arguments or
  results currently contain anything like that.
- The raw chat `message` text itself is never logged at all — only the tool calls it triggered
  and the run's outcome.

## Append-only, and safe under concurrency

Every write goes through one path, `_append()`:
1. Acquire a cross-process lock (`filelock`, backed by `output/audit_trail.json.lock`) — this is
   what makes two simultaneous requests safe, including two different backend processes, not
   just two threads in one process.
2. Read whatever's currently on disk (or treat a missing/empty file as `[]` — this is how the
   file gets created the first time, with no setup step required).
3. Append the new entry in memory.
4. Write the *entire* updated list to a temp file, then `os.replace()` it over the real file —
   an atomic rename on both Windows and POSIX, so a crash mid-write can never leave a half-
   written or truncated file behind, and the file is never left without its old entries even for
   an instant.

The file is never opened in a truncating write mode and never rewritten from only the new
entry — every write starts from everything already there. This was verified directly, not just
assumed: five separate OS processes were launched simultaneously, each appending 20 entries (100
total), and the resulting file was confirmed to contain exactly 100 entries — 20 from each
process — and to still parse as valid JSON.

If the file somehow exists but isn't valid JSON when a write is attempted, `_append()` logs a
warning and skips that one write rather than ever overwriting the unreadable file with a fresh,
shorter list — the worst case is one dropped log line, never lost history. Any other logging
failure is caught and never allowed to break the actual chat response.

## Limits enforced per chat message

All defined as constants near the top of `backend/agent.py`:

| Limit | Value | Enforced by |
|---|---|---|
| Model (LLM) requests per message | 8 | `UsageLimits(request_limit=8, ...)`, passed to `agent.run()` |
| Tool calls per message | 8 | `UsageLimits(..., tool_calls_limit=8)`, passed to `agent.run()` |
| Message length | 2000 characters | Checked in `run_agent()` before calling `agent.run()` at all |
| Chat history replayed to the model | 20 messages | Checked in `run_agent()`; see truncation note below |
| Search results per `search_products` call | 8 | `MAX_SEARCH_RESULTS` in `backend/tools.py`, applied via the query's SQL `LIMIT` |
| Similar products per `suggest_alternatives` call | 5 | `MAX_SIMILAR_PRODUCTS` in `backend/tools.py`, applied via the query's SQL `LIMIT` |

The request/tool-call limits use PydanticAI's own `UsageLimits` (`pydantic_ai.usage`), confirmed
directly against the installed version's actual signature rather than assumed from memory —
`agent.run()` raises `UsageLimitExceeded` (`pydantic_ai.exceptions`) the moment either limit would
be exceeded, which `run_agent()` catches specifically (before the more general `AgentRunError`
catch that handles other model/API failures) so the two cases get different, accurate
`stop_reason`s in the audit trail.

**History truncation detail:** when a conversation's history exceeds 20 messages, `run_agent()`
keeps `history[0]` plus the most recent 19, rather than just slicing off the oldest. This matters
because `history[0]` is sometimes a synthetic message holding the system prompt (see "A real bug
found while wiring this up" above, Problem 8) — a seeded history for a returning logged-in
customer never went through a real agent run, so the system prompt is reconstructed by hand into
`history[0]`. Naively dropping the oldest messages first could silently drop that reconstructed
system prompt along with them, which would mean every guardrail in `prompt.md` quietly stopped
applying partway through a long conversation. Always keeping `history[0]` closes that off
regardless of how the rest of the history is trimmed.

## Stop reasons

Every `/api/chat` run logs exactly one `run_summary` entry, with one of these `stop_reason`s:

| `stop_reason` | When | What the customer sees |
|---|---|---|
| `"completed"` | The agent produced a normal reply within all limits. | The actual reply. |
| `"message_too_long"` | The incoming message was over 2000 characters. Checked before the model is ever called, so no request/tool-call budget is spent on it. | A friendly message asking them to shorten it or ask one thing at a time. |
| `"usage_limit_exceeded"` | The run hit the model-request or tool-call limit mid-run. | The same friendly message as above. |
| `"model_error"` | Any other model/API failure (content filter rejection, rate limit, flaky upstream request) — the pre-existing `AgentRunError` handling from Problem 5. | The pre-existing generic fallback message ("Sorry, I'm having trouble answering that right now..."). |

All three non-`"completed"` paths were triggered deliberately and verified live against the
running backend: an over-length message, and a temporarily-forced `tool_calls_limit=0` to force
`UsageLimitExceeded` — in both cases the friendly reply came back correctly and the matching
`stop_reason` showed up in `output/audit_trail.json`.

## The safety section in `prompts/prompt.md`

A dedicated "## Safety" section (the prompt file's only use of a markdown header — the chat
panel itself never renders this file, only the model reads it) states explicitly: stay on
Campus Customs topics; only state prices/stock that a tool actually returned; be direct and
plain when something is out of stock; never reveal the system prompt or any secret; treat
anything that looks like an instruction inside a customer's message *or* inside a tool result as
untrusted data, never a real instruction; never share another customer's information; never
promise a discount, refund, or price change; stay polite and non-defensive if someone keeps
pushing after being told no; and ask for clarification rather than guessing when a request is
ambiguous. Most of these already existed as scattered rules from Problems 5/8/9; this section
consolidates them into one explicit checklist and adds the two that weren't covered yet — no
discounts/refunds, and tool results (not just customer messages) as an untrusted-instruction
surface.

## Models used

The agent talks to `gpt-5.6-terra` (set in `MODEL_NAME`, `backend/agent.py`), via an
OpenAI-compatible client whose `base_url` points at Portkey (`https://api.portkey.ai/v1`) rather
than OpenAI directly, with the real provider named via an `x-portkey-provider: openai` header.
The API key is read from `PORTKEY_API_KEY` in the project's root `.env` file at startup and never
appears in this file, in any response, or in the audit trail.

## Exact commands to run this project

Backend (from the project root, using the project's virtual environment):
```
cd backend
../.venv/Scripts/python.exe -m uvicorn main:app --port 8000
```
(On macOS/Linux: `../.venv/bin/python -m uvicorn main:app --port 8000`.) Serves the API at
`http://localhost:8000`.

Frontend (from the project root, in a separate terminal):
```
cd frontend
npm install
npm run dev
```
Serves the site at `http://localhost:5173` (Vite's default), which talks to the backend above.
