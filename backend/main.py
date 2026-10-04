"""Campus Customs backend.

A small FastAPI app that reads product and inventory data out of the
project's SQLite database (data/campus_customs.db) and serves product
images (data/products/). The product/inventory endpoints in this file
only ever read from the database — every connection they open uses
SQLite's read-only URI mode, so even a bug here can't accidentally write
to it. The only part of this backend that writes to the database is
`auth.py`'s signup endpoint, which only ever inserts into `users`.
"""

import json
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import get_current_user, router as auth_router
from agent import run_agent
from chat_history import get_recent_history
from models import AuthenticatedUser, ChatHistoryMessage, ChatRequest, ChatResponse

# --- paths -------------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
PRODUCTS_DIR = DATA_DIR / "products"


def get_connection() -> sqlite3.Connection:
    """Open the database read-only. Any attempted write raises sqlite3.OperationalError."""
    uri = f"file:{DB_PATH.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# --- response models -----------------------------------------------------

class ProductSummary(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    image_url: str


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductDetail(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float
    image_url: str
    sizes: list[SizeStock]
    total_stock: int


# --- app setup -----------------------------------------------------------

app = FastAPI(title="Campus Customs API")

# Allow the React dev server (Vite) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(auth_router)

# Serve product images at /media/products/<file>.jpg
app.mount("/media/products", StaticFiles(directory=PRODUCTS_DIR), name="products")


def _image_url(image_file_path: str) -> str:
    """catalogue.image_file_path looks like 'products/<file>.jpg' already."""
    filename = Path(image_file_path).name
    return f"/media/products/{filename}"


# --- endpoints -------------------------------------------------------------

@app.get("/api/products", response_model=list[ProductSummary])
def list_products():
    """All products in the catalogue."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT product_id, name, garment_type, description, price, image_file_path
            FROM catalogue
            ORDER BY name
            """
        ).fetchall()
    finally:
        conn.close()

    return [
        ProductSummary(
            product_id=row["product_id"],
            name=row["name"],
            garment_type=row["garment_type"],
            description=row["description"],
            price=row["price"],
            image_url=_image_url(row["image_file_path"]),
        )
        for row in rows
    ]


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str):
    """A single product, with its sizes and stock from the inventory table."""
    conn = get_connection()
    try:
        product_row = conn.execute(
            """
            SELECT product_id, name, garment_type, description, colors, price, image_file_path
            FROM catalogue
            WHERE product_id = ?
            """,
            (product_id,),
        ).fetchone()

        if product_row is None:
            raise HTTPException(status_code=404, detail="Product not found")

        inventory_rows = conn.execute(
            """
            SELECT size, quantity
            FROM inventory
            WHERE product_id = ?
            ORDER BY id
            """,
            (product_id,),
        ).fetchall()
    finally:
        conn.close()

    sizes = [SizeStock(size=row["size"], quantity=row["quantity"]) for row in inventory_rows]

    return ProductDetail(
        product_id=product_row["product_id"],
        name=product_row["name"],
        garment_type=product_row["garment_type"],
        description=product_row["description"],
        colors=json.loads(product_row["colors"]),
        price=product_row["price"],
        image_url=_image_url(product_row["image_file_path"]),
        sizes=sizes,
        total_stock=sum(s.quantity for s in sizes),
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, current_user: AuthenticatedUser | None = Depends(get_current_user)):
    """Runs the user's message through the PydanticAI agent and returns its reply.

    Pass back the conversation_id from a prior reply to continue that
    conversation with its history intact; omit it to start a new one.

    Who's asking is determined entirely from the Authorization header's
    session token (see auth.get_current_user) — never from anything else
    in the request body. Guests (no valid token) can still chat; nothing
    is saved for them. Logged-in customers' messages are saved, and a
    brand-new conversation is seeded with their past history.
    """
    return await run_agent(body.message, body.conversation_id, current_user, body.page_product_id)


@app.get("/api/chat/history", response_model=list[ChatHistoryMessage])
def chat_history(current_user: AuthenticatedUser | None = Depends(get_current_user)):
    """A logged-in customer's recent saved chat messages, oldest first.
    Requires a valid session token — there's no history to return for a guest."""
    if current_user is None:
        raise HTTPException(status_code=401, detail="Log in to view chat history.")
    return get_recent_history(current_user.id)


@app.get("/api/health")
def health():
    return {"status": "ok"}
