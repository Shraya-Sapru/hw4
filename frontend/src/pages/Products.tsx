import { useEffect, useMemo, useState } from "react";
import CatalogueCard from "../components/CatalogueCard";
import { fetchProducts, type ProductSummary } from "../lib/api";
import { clearChatSearchState } from "../lib/chatSearchResults";
import { useChatSearch } from "../lib/useChatSearch";
import { categorize } from "../lib/productCategory";
import "./Products.css";

type LoadState = "loading" | "error" | "ready";

const ALL_CATEGORIES = "All";

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** A regex matching `word` as a whole word, not merely as a substring
 * somewhere inside a longer word. Without this, searching "tshirt"
 * would (and did) incorrectly match "sweatshirt" — "tshirt" is a
 * literal substring of "sweatshirt" (swea-TSHIRT). Hyphens are
 * stripped from the word first, matching how the haystack is
 * normalized below, so a hyphenated query word still lines up. */
function wordBoundaryPattern(word: string): RegExp {
  return new RegExp(`\\b${escapeRegExp(word.replace(/-/g, ""))}\\b`, "i");
}

/** Splits the query into words and requires every word to appear
 * somewhere in the product's searchable text — matches the same
 * forgiving approach the chatbot's own search_products tool uses
 * (including the plural/singular fallback and whole-word matching),
 * so a shopper gets the same quality of search whether they type it
 * or ask the chatbot. */
function matchesSearch(product: ProductSummary, query: string): boolean {
  const words = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length === 0) return true;

  // Hyphens stripped here too, so "t shirt" / "t-shirt" / "tshirt" in
  // the catalogue text all line up with a query word the same way.
  const haystack = `${product.name} ${product.description} ${product.garment_type}`
    .toLowerCase()
    .replace(/-/g, "");

  return words.every((word) => {
    if (wordBoundaryPattern(word).test(haystack)) return true;
    const altForm = word.endsWith("s") && word.length > 3 ? word.slice(0, -1) : `${word}s`;
    return wordBoundaryPattern(altForm).test(haystack);
  });
}

export default function Products() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [state, setState] = useState<LoadState>("loading");
  const chatSearch = useChatSearch();

  const [searchQuery, setSearchQuery] = useState("");
  const [category, setCategory] = useState(ALL_CATEGORIES);
  const [minPrice, setMinPrice] = useState<number | "">("");
  const [maxPrice, setMaxPrice] = useState<number | "">("");

  useEffect(() => {
    let cancelled = false;

    fetchProducts()
      .then((data) => {
        if (cancelled) return;
        setProducts(data);
        setState("ready");
      })
      .catch(() => {
        if (cancelled) return;
        setState("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const categories = useMemo(() => {
    const found = new Set(products.map((p) => categorize(p.garment_type)));
    return [ALL_CATEGORIES, ...Array.from(found).sort()];
  }, [products]);

  const filteredProducts = useMemo(() => {
    return products.filter((product) => {
      if (category !== ALL_CATEGORIES && categorize(product.garment_type) !== category) {
        return false;
      }
      if (minPrice !== "" && product.price < minPrice) return false;
      if (maxPrice !== "" && product.price > maxPrice) return false;
      if (!matchesSearch(product, searchQuery)) return false;
      return true;
    });
  }, [products, category, minPrice, maxPrice, searchQuery]);

  const hasActiveFilters = searchQuery.trim() !== "" || category !== ALL_CATEGORIES || minPrice !== "" || maxPrice !== "";

  function clearFilters() {
    setSearchQuery("");
    setCategory(ALL_CATEGORIES);
    setMinPrice("");
    setMaxPrice("");
  }

  // A chat search is active: show those results instead of the full
  // catalogue, with a way back to the full list.
  if (chatSearch) {
    return (
      <div className="products-page">
        <div className="products-page__header">
          <h1>Chat Search Results</h1>
          <p>{chatSearch.message}</p>
          <button
            type="button"
            className="products-page__clear"
            onClick={clearChatSearchState}
          >
            ← Show all products
          </button>
        </div>

        {chatSearch.products.length === 0 ? (
          <p className="products-page__status">
            No matching products found. Try asking the chat about something else, or{" "}
            <button
              type="button"
              className="products-page__clear-inline"
              onClick={clearChatSearchState}
            >
              browse the full catalogue
            </button>
            .
          </p>
        ) : (
          <div className="products-page__grid">
            {chatSearch.products.map((product) => (
              <CatalogueCard key={product.product_id} product={product} />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="products-page">
      <div className="products-page__header">
        <h1>All Products</h1>
        <p>Every piece we carry, fresh from the Campus Customs catalogue.</p>
      </div>

      {state === "ready" && (
        <div className="products-page__filters">
          <input
            type="search"
            className="products-page__search"
            placeholder="Search products…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            aria-label="Search products"
          />

          <select
            className="products-page__select"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            aria-label="Filter by category"
          >
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          <div className="products-page__price-range">
            <label>
              Min $
              <input
                type="number"
                min={0}
                value={minPrice}
                onChange={(e) => setMinPrice(e.target.value === "" ? "" : Number(e.target.value))}
                aria-label="Minimum price"
              />
            </label>
            <label>
              Max $
              <input
                type="number"
                min={0}
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value === "" ? "" : Number(e.target.value))}
                aria-label="Maximum price"
              />
            </label>
          </div>

          {hasActiveFilters && (
            <button type="button" className="products-page__clear" onClick={clearFilters}>
              Clear filters
            </button>
          )}
        </div>
      )}

      {state === "loading" && <p className="products-page__status">Loading products…</p>}

      {state === "error" && (
        <p className="products-page__status products-page__status--error">
          Couldn't load products. Make sure the backend is running at
          http://localhost:8000.
        </p>
      )}

      {state === "ready" && filteredProducts.length === 0 && (
        <p className="products-page__status">
          No products match your search and filters.{" "}
          <button type="button" className="products-page__clear-inline" onClick={clearFilters}>
            Clear filters
          </button>{" "}
          to see everything.
        </p>
      )}

      {state === "ready" && filteredProducts.length > 0 && (
        <div className="products-page__grid">
          {filteredProducts.map((product) => (
            <CatalogueCard key={product.product_id} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
