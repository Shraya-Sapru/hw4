"""Agent tools — read-only lookups against data/campus_customs.db.

Every connection here is opened in SQLite's read-only URI mode, and every
query uses `?` parameterized placeholders — the same guarantees as the
rest of the backend. Nothing in this file ever writes to the database.

The database path is built from this file's own location
(`Path(__file__)`), not the process's working directory, so these tools
work correctly whether the backend is started from inside `backend/` (as
intended) or anywhere else.
"""

import functools
import inspect
import json
import re
import sqlite3
from pathlib import Path

from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry

from audit import log_tool_call
from deps import ChatDeps
from models import (
    AlternativesResult,
    ProductCard,
    ProductDetails,
    ProductLookupResult,
    ProductSearchResult,
    StockCheckResult,
    StockLevel,
)


def _audited(fn):
    """Wraps a tool so every call is recorded to the audit trail, with the
    conversation_id pulled off ctx.deps (set by agent.py before each run).

    Uses functools.wraps so the wrapper's signature — which pydantic-ai
    inspects to decide whether a tool needs a RunContext injected — still
    matches the original function exactly; only the body changes.
    """
    takes_ctx = "ctx" in inspect.signature(fn).parameters

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        bound = inspect.signature(fn).bind(*args, **kwargs)
        bound.apply_defaults()
        call_args = {k: v for k, v in bound.arguments.items() if k != "ctx"}
        conversation_id = bound.arguments["ctx"].deps.conversation_id if takes_ctx else None

        result = fn(*args, **kwargs)
        log_tool_call(conversation_id or "unknown", fn.__name__, call_args, result.model_dump())
        return result

    return wrapper

BACKEND_DIR = Path(__file__).resolve().parent
DB_PATH = BACKEND_DIR.parent / "data" / "campus_customs.db"

MAX_SEARCH_RESULTS = 8


def _regexp(pattern: str, value: object) -> bool:
    """Backs the custom SQLite REGEXP operator used by search_products.
    Hyphens are stripped from the column value before matching, so a
    query normalized the same way (see _word_boundary_pattern) lines up
    with catalogue text regardless of how it's hyphenated — "t shirt" /
    "t-shirt" / "tshirt" all end up comparable."""
    if value is None:
        return False
    normalized = str(value).replace("-", "")
    return re.search(pattern, normalized, re.IGNORECASE) is not None


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.create_function("REGEXP", 2, _regexp)
    return conn


def _word_boundary_pattern(word: str) -> str:
    """A regex pattern matching `word` as a whole word, not merely as a
    substring somewhere inside a longer word. Without this, searching
    "tshirt" would (and did) incorrectly match "sweatshirt" — "tshirt"
    is a literal substring of "sweatshirt" (swea-TSHIRT). Hyphens are
    stripped from the word too, matching how _regexp treats the column
    text, so a hyphenated query word still lines up correctly."""
    return r"\b" + re.escape(word.replace("-", "")) + r"\b"


def _image_url(image_file_path: str) -> str:
    """catalogue.image_file_path looks like 'products/<file>.jpg' already."""
    return f"/media/products/{Path(image_file_path).name}"


def _row_to_card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        price=row["price"],
        image_url=_image_url(row["image_file_path"]),
        description=row["description"],
    )


def search_products(ctx: RunContext[ChatDeps], query: str) -> ProductSearchResult:
    """Search the catalogue by name or keyword.

    Matches against the product name, description, garment type, and
    search tags. Use this whenever someone describes what they're looking
    for in words (a team, a style, a sport, a color) rather than naming
    an exact product.

    Args:
        query: What to search for, e.g. "hoodie", "Yale baseball", "navy crewneck".
            Doesn't need to match the product name exactly — each word in
            the query is matched independently, so "forest hoodie" still
            finds "The Forest School Hoodie" even though "School" sits
            between those two words in the real name. Singular and plural
            forms both work too (e.g. "hoodies" still matches "hoodie"),
            and hyphenation doesn't matter ("tshirt" / "t-shirt" / "t
            shirt" all match the same way). Matches whole words only —
            searching "tshirt" won't match "sweatshirt" just because one
            is a substring of the other.
    """
    words = [w for w in query.strip().split() if w]
    if not words:
        return ProductSearchResult(query=query, found=False, matches=[])

    # Require every word to appear *somewhere* (any of these columns, not
    # necessarily the same one, and not necessarily adjacent) rather than
    # requiring the whole query as one literal contiguous phrase — that's
    # what lets a loosely-worded query like "forest hoodie" still match
    # "The Forest School Hoodie".
    conditions = []
    params: list[str] = []
    for word in words:
        # Also try the other simple plural/singular form of the word, so a
        # tool caller doesn't need to get pluralization exactly right —
        # "hoodies" still matches catalogue text that only ever says
        # "hoodie". This is a plain heuristic (strip/add a trailing "s"),
        # not real stemming, which is enough for ordinary English nouns.
        word_forms = {word}
        if word.endswith("s") and len(word) > 3:
            word_forms.add(word[:-1])
        else:
            word_forms.add(word + "s")

        word_conditions = []
        for form in word_forms:
            pattern = _word_boundary_pattern(form)
            word_conditions.append(
                "(name REGEXP ? OR description REGEXP ? OR garment_type REGEXP ? OR search_tags REGEXP ?)"
            )
            params.extend([pattern, pattern, pattern, pattern])
        conditions.append(f"({' OR '.join(word_conditions)})")

    where_clause = " AND ".join(conditions)
    params.append(MAX_SEARCH_RESULTS)

    conn = _get_connection()
    try:
        rows = conn.execute(
            f"""
            SELECT product_id, name, garment_type, description, price, image_file_path
            FROM catalogue
            WHERE {where_clause}
            ORDER BY name
            LIMIT ?
            """,
            params,
        ).fetchall()
    finally:
        conn.close()

    matches = [_row_to_card(row) for row in rows]
    return ProductSearchResult(query=query, found=len(matches) > 0, matches=matches)


def get_product_details(
    ctx: RunContext[ChatDeps], product_id: str | None = None
) -> ProductLookupResult:
    """Get a product's full description, price, and colors.

    Args:
        product_id: The exact product_id, e.g. "basic-hoodie-big-yale".
            Get this from a prior search_products call — don't guess one.
            Leave unset to use the product the customer is currently
            viewing on the website (if any) — useful for something like
            "do you have this in pink?" where they didn't name the item.
    """
    effective_id = product_id or ctx.deps.product_context_id
    if effective_id is None:
        raise ModelRetry(
            "No product_id was given, and the customer isn't on a specific product's "
            "page right now, so there's nothing to look up. Ask them which item they mean."
        )

    conn = _get_connection()
    try:
        row = conn.execute(
            """
            SELECT product_id, name, garment_type, description, colors, price, image_file_path
            FROM catalogue
            WHERE product_id = ?
            """,
            (effective_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return ProductLookupResult(found=False, product=None)

    product = ProductDetails(
        product_id=row["product_id"],
        name=row["name"],
        garment_type=row["garment_type"],
        description=row["description"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        image_url=_image_url(row["image_file_path"]),
    )
    return ProductLookupResult(found=True, product=product)


def check_stock(
    ctx: RunContext[ChatDeps], product_id: str | None = None, size: str | None = None
) -> StockCheckResult:
    """Check stock for a product, for one size or for every size.

    Args:
        product_id: The exact product_id, e.g. "basic-hoodie-big-yale".
            Get this from a prior search_products call — don't guess one.
            Leave unset to use the product the customer is currently
            viewing on the website (if any) — useful for something like
            "is this in stock in large?" where they didn't name the item.
        size: A specific size like "M" or "XL" to check just that size.
            Leave unset to get every size's stock at once.
    """
    effective_id = product_id or ctx.deps.product_context_id
    if effective_id is None:
        raise ModelRetry(
            "No product_id was given, and the customer isn't on a specific product's "
            "page right now, so there's nothing to check stock for. Ask them which item they mean."
        )

    conn = _get_connection()
    try:
        product_row = conn.execute(
            "SELECT 1 FROM catalogue WHERE product_id = ?", (effective_id,)
        ).fetchone()

        if product_row is None:
            return StockCheckResult(
                product_found=False, product_id=effective_id, size_requested=size, sizes=[]
            )

        if size is not None:
            inventory_rows = conn.execute(
                "SELECT size, quantity FROM inventory WHERE product_id = ? AND upper(size) = upper(?)",
                (effective_id, size),
            ).fetchall()
        else:
            inventory_rows = conn.execute(
                "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id",
                (effective_id,),
            ).fetchall()
    finally:
        conn.close()

    sizes = [
        StockLevel(size=row["size"], quantity=row["quantity"], in_stock=row["quantity"] > 0)
        for row in inventory_rows
    ]
    return StockCheckResult(
        product_found=True, product_id=effective_id, size_requested=size, sizes=sizes
    )


MAX_SIMILAR_PRODUCTS = 5


def suggest_alternatives(
    ctx: RunContext[ChatDeps], product_id: str | None = None
) -> AlternativesResult:
    """Find real alternatives when a product or size is out of stock.

    Looks for two kinds of alternative, always from actual current data:
    other sizes of this same product that ARE in stock, and other
    products of the same garment type that have at least one size in
    stock. Use this right after check_stock shows something as out of
    stock, instead of just leaving the customer with a dead end.

    Args:
        product_id: The exact product_id, e.g. "basic-hoodie-big-yale".
            Leave unset to use the product the customer is currently
            viewing on the website (if any).
    """
    effective_id = product_id or ctx.deps.product_context_id
    if effective_id is None:
        raise ModelRetry(
            "No product_id was given, and the customer isn't on a specific product's "
            "page right now, so there's nothing to find alternatives for. Ask them which item they mean."
        )

    conn = _get_connection()
    try:
        product_row = conn.execute(
            "SELECT garment_type FROM catalogue WHERE product_id = ?", (effective_id,)
        ).fetchone()

        if product_row is None:
            return AlternativesResult(
                product_found=False, other_in_stock_sizes=[], similar_in_stock_products=[]
            )

        inventory_rows = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? AND quantity > 0 ORDER BY id",
            (effective_id,),
        ).fetchall()

        similar_rows = conn.execute(
            """
            SELECT DISTINCT c.product_id, c.name, c.price, c.image_file_path, c.description
            FROM catalogue c
            JOIN inventory i ON i.product_id = c.product_id
            WHERE c.garment_type = ? AND c.product_id != ? AND i.quantity > 0
            ORDER BY c.name
            LIMIT ?
            """,
            (product_row["garment_type"], effective_id, MAX_SIMILAR_PRODUCTS),
        ).fetchall()
    finally:
        conn.close()

    other_in_stock_sizes = [
        StockLevel(size=row["size"], quantity=row["quantity"], in_stock=True)
        for row in inventory_rows
    ]
    similar_in_stock_products = [_row_to_card(row) for row in similar_rows]

    return AlternativesResult(
        product_found=True,
        other_in_stock_sizes=other_in_stock_sizes,
        similar_in_stock_products=similar_in_stock_products,
    )


TOOLS = [
    _audited(search_products),
    _audited(get_product_details),
    _audited(check_stock),
    _audited(suggest_alternatives),
]
