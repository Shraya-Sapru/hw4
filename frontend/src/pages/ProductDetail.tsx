import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct, imageUrl, type ProductDetail as ProductDetailType, type SizeStock } from "../lib/api";
import "./ProductDetail.css";

type LoadState = "loading" | "error" | "ready";

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>();
  const [product, setProduct] = useState<ProductDetailType | null>(null);
  const [state, setState] = useState<LoadState>("loading");
  const [selectedSize, setSelectedSize] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    let cancelled = false;

    setState("loading");
    setSelectedSize(null);
    fetchProduct(productId)
      .then((data) => {
        if (cancelled) return;
        setProduct(data);
        setState("ready");
        // Default to the first in-stock size, if there is one, so there's
        // something useful shown right away rather than an empty prompt.
        const firstInStock = data.sizes.find((s) => s.quantity > 0);
        setSelectedSize(firstInStock?.size ?? null);
      })
      .catch(() => {
        if (cancelled) return;
        setState("error");
      });

    return () => {
      cancelled = true;
    };
  }, [productId]);

  if (state === "loading") {
    return <p className="product-detail__status">Loading product…</p>;
  }

  if (state === "error" || !product) {
    return (
      <div className="product-detail__status">
        <p>Couldn't find that product.</p>
        <Link to="/products">← Back to all products</Link>
      </div>
    );
  }

  const selected: SizeStock | undefined = product.sizes.find((s) => s.size === selectedSize);

  return (
    <div className="product-detail">
      <div className="product-detail__image">
        <img src={imageUrl(product.image_url)} alt={product.name} />
      </div>

      <div className="product-detail__info">
        <Link to="/products" className="product-detail__back">
          ← All products
        </Link>
        <h1>{product.name}</h1>
        <p className="product-detail__price">${product.price.toFixed(2)}</p>
        <p className="product-detail__description">{product.description}</p>

        <div className="product-detail__colors">
          <h2>Colors</h2>
          <p>{product.colors.join(", ")}</p>
        </div>

        <div className="product-detail__sizes">
          <h2>Sizes</h2>
          <div className="product-detail__size-buttons">
            {product.sizes.map((s) => {
              const outOfStock = s.quantity === 0;
              const isSelected = s.size === selectedSize;
              return (
                <button
                  key={s.size}
                  type="button"
                  className={[
                    "product-detail__size-button",
                    outOfStock ? "product-detail__size-button--out-of-stock" : "",
                    isSelected ? "product-detail__size-button--selected" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setSelectedSize(s.size)}
                  aria-pressed={isSelected}
                >
                  <span>{s.size}</span>
                  {outOfStock && <span className="product-detail__size-badge">Sold out</span>}
                </button>
              );
            })}
          </div>

          <p className="product-detail__stock-line" aria-live="polite">
            {selected ? (
              selected.quantity > 0 ? (
                <>
                  Size <strong>{selected.size}</strong>: {selected.quantity} in stock
                </>
              ) : (
                <>
                  Size <strong>{selected.size}</strong> is currently sold out.
                </>
              )
            ) : (
              "Select a size above to see its stock."
            )}
          </p>

          <p className="product-detail__total">{product.total_stock} total in stock, all sizes</p>
        </div>
      </div>
    </div>
  );
}
