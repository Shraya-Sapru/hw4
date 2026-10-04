"""Shared data shapes for the chat agent."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """What the frontend sends to POST /api/chat."""

    message: str
    conversation_id: str | None = None
    """Echo back the conversation_id from the previous reply to continue
    the same conversation. Leave unset to start a new one."""

    page_product_id: str | None = None
    """The product_id of the page the customer is currently on, if any
    (e.g. sent when they're viewing /products/<id>). Lets the agent
    resolve "do you have this in pink?" without them naming the item."""


class CustomerInfo(BaseModel):
    """What the agent is allowed to know about who it's talking to.
    Deliberately just a name and email — never a password hash, a user
    id, or anything belonging to a different user."""

    first_name: str
    last_name: str
    email: str


class AuthenticatedUser(BaseModel):
    """Internal use only (backend/auth.py, backend/main.py) — includes the
    numeric id so the backend can save/load that user's own chat history.
    This type is never sent to the agent or returned in any response;
    CustomerInfo (above) is what the agent actually sees."""

    id: int
    first_name: str
    last_name: str
    email: str


class ChatHistoryMessage(BaseModel):
    """One saved message, as returned by GET /api/chat/history."""

    role: str
    content: str
    created_at: str


class ProductCard(BaseModel):
    """A product the agent wants to show alongside its reply, e.g. when it
    mentions or recommends something from the catalogue."""

    product_id: str
    name: str
    price: float
    image_url: str
    description: str


class ChatReply(BaseModel):
    """The agent's structured output type — the agent fills this in
    directly rather than just returning plain text, so it can attach
    product cards once tools.py actually knows how to look products up.
    Deliberately has no conversation_id field: the model has no business
    generating that itself, so it's added separately in ChatResponse.

    `products` is always a list, never null — an empty list means either
    "this wasn't a product question" or "it was, but nothing matched."
    Always being a list (not optional) means the frontend never has to
    branch on null vs. empty; it's one shape either way."""

    message: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """What POST /api/chat actually returns to the frontend: the agent's
    reply, plus the conversation_id to send back on the next message so
    the conversation keeps its memory."""

    message: str
    products: list[ProductCard] = Field(default_factory=list)
    conversation_id: str


# --- tool result types (backend/tools.py) -----------------------------------
#
# Every tool result below carries an explicit `found`/`product_found` flag
# rather than leaving the agent to infer "not found" from an empty list or
# a null field. That's deliberate: an explicit boolean is something the
# model can check directly and reliably, instead of having to reason about
# whether an empty collection means "nothing matched" versus "this product
# just happens to have no sizes" — one less place for it to guess.


class ProductSearchResult(BaseModel):
    """Result of searching the catalogue by name or keyword."""

    query: str
    found: bool
    matches: list[ProductCard]


class ProductDetails(BaseModel):
    """Full description/price details for one product."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    colors: list[str]
    image_url: str


class ProductLookupResult(BaseModel):
    """Result of looking up a single product's description and price."""

    found: bool
    product: ProductDetails | None = None


class StockLevel(BaseModel):
    """Stock for one size of one product.

    Includes both the raw `quantity` and a derived `in_stock` flag on
    purpose: `quantity` is the real number for when someone asks "how many
    are left", while `in_stock` is a plain yes/no the agent can use
    directly to say "that's out of stock" without doing its own
    quantity > 0 comparison (and risking getting that comparison wrong).
    """

    size: str
    quantity: int
    in_stock: bool


class StockCheckResult(BaseModel):
    """Result of checking stock for a product, for one size or all sizes.

    `sizes` being empty has two different meanings depending on
    `product_found`:
      - `product_found` is False: the product itself doesn't exist.
      - `product_found` is True, a specific `size_requested` was given,
        and `sizes` is still empty: the product exists, but doesn't come
        in that size at all (different from being out of stock in it —
        that case instead returns one `StockLevel` with `in_stock=False`).
    """

    product_found: bool
    product_id: str
    size_requested: str | None
    sizes: list[StockLevel]


class AlternativesResult(BaseModel):
    """Result of looking for alternatives when something's out of stock.

    Two different kinds of alternative, both drawn from real data only:
      - `other_in_stock_sizes`: other sizes of this *same* product that
        are actually in stock — useful when one specific size is out.
      - `similar_in_stock_products`: other products of the same garment
        type that have at least one size in stock — useful when the
        whole product (or the only size that mattered) is out entirely.
    Either or both can be empty if there's genuinely nothing to suggest;
    that's a real "we don't have an alternative," not a failure.
    """

    product_found: bool
    other_in_stock_sizes: list[StockLevel]
    similar_in_stock_products: list[ProductCard]
