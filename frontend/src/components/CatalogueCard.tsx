import { Link } from "react-router-dom";
import { imageUrl, type DisplayProduct } from "../lib/api";
import "./CatalogueCard.css";

interface CatalogueCardProps {
  product: DisplayProduct;
}

export default function CatalogueCard({ product }: CatalogueCardProps) {
  return (
    <Link to={`/products/${product.product_id}`} className="catalogue-card">
      <div className="catalogue-card__image">
        <img src={imageUrl(product.image_url)} alt={product.name} loading="lazy" />
        <span className="catalogue-card__sparkle" aria-hidden="true">
          ✦
        </span>
      </div>
      <div className="catalogue-card__body">
        <h3 className="catalogue-card__name">{product.name}</h3>
        <p className="catalogue-card__description">{product.description}</p>
        <p className="catalogue-card__price">${product.price.toFixed(2)}</p>
      </div>
    </Link>
  );
}
