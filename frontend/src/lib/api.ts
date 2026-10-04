// Base URL for the Campus Customs FastAPI backend (see backend/main.py).
export const API_BASE_URL = "http://localhost:8000";

export interface ProductSummary {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  price: number;
  image_url: string;
}

/** The minimal shape a product card actually needs to render. Both
 * ProductSummary (from /api/products) and the chatbot's ChatProductCard
 * (from /api/chat) satisfy this, so CatalogueCard can render either
 * without caring which one it got. */
export interface DisplayProduct {
  product_id: string;
  name: string;
  price: number;
  image_url: string;
  description: string;
}

export interface SizeStock {
  size: string;
  quantity: number;
}

export interface ProductDetail extends ProductSummary {
  colors: string[];
  sizes: SizeStock[];
  total_stock: number;
}

export async function fetchProducts(): Promise<ProductSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/products`);
  if (!response.ok) {
    throw new Error(`Failed to load products (${response.status})`);
  }
  return response.json();
}

export async function fetchProduct(productId: string): Promise<ProductDetail> {
  const response = await fetch(`${API_BASE_URL}/api/products/${productId}`);
  if (!response.ok) {
    throw new Error(`Failed to load product "${productId}" (${response.status})`);
  }
  return response.json();
}

export function imageUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}
