import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import CatalogueCard from "../components/CatalogueCard";
import Mascot from "../components/Mascot";
import { fetchProducts, type ProductSummary } from "../lib/api";
import "./Home.css";

const FAN_FAVORITE_COUNT = 4;

export default function Home() {
  const [favorites, setFavorites] = useState<ProductSummary[]>([]);
  const [loadState, setLoadState] = useState<"loading" | "error" | "ready">("loading");

  useEffect(() => {
    let cancelled = false;

    fetchProducts()
      .then((all) => {
        if (cancelled) return;
        setFavorites(all.slice(0, FAN_FAVORITE_COUNT));
        setLoadState("ready");
      })
      .catch(() => {
        if (cancelled) return;
        setLoadState("error");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="home">
      <section className="hero">
        <div className="hero__content">
          <p className="hero__eyebrow">Campus Customs</p>
          <h1 className="hero__title">
            <span className="hero__sparkle hero__sparkle--1" aria-hidden="true">
              ✦
            </span>
            WEAR YOUR PRIDE, EVERY DAY.
            <span className="hero__sparkle hero__sparkle--2" aria-hidden="true">
              ✦
            </span>
          </h1>
          <p className="hero__subtitle">
            Hoodies, tees, and everyday essentials for students, alumni,
            and fans who never stopped bleeding blue.
          </p>
          <Link to="/products" className="hero__cta">
            Shop All
          </Link>
        </div>
        <div className="hero__mascot" aria-hidden="true">
          <Mascot size={180} />
        </div>
      </section>

      <section className="featured">
        <div className="featured__header">
          <div>
            <p className="featured__eyebrow">New &amp; Noteworthy</p>
            <h2>Fan Favorites</h2>
          </div>
          <Link to="/products" className="featured__link">
            View all products →
          </Link>
        </div>

        {loadState === "loading" && <p className="featured__status">Loading favorites…</p>}
        {loadState === "error" && (
          <p className="featured__status">
            Couldn't load favorites right now — check out the{" "}
            <Link to="/products">full catalogue</Link> instead.
          </p>
        )}
        {loadState === "ready" && (
          <div className="featured__grid">
            {favorites.map((product) => (
              <CatalogueCard key={product.product_id} product={product} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
