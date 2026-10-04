// The catalogue's own `garment_type` values are too granular and
// inconsistent for a shopper-facing filter (e.g. "crewneck sweatshirt",
// "quarter-zip pullover sweatshirt", "hooded pullover sweatshirt" are all
// slightly different strings for closely related items). This buckets
// them into a small set of categories a shopper would actually recognize,
// purely for the Products page filter — the real garment_type is still
// what's stored and shown everywhere else.

// Order matters: "sweatshirt" literally contains "shirt" as a substring,
// so the crewneck/sweatshirt rule has to be checked before the generic
// "shirt" rule, or every sweatshirt gets miscategorized as a plain Shirt.
const CATEGORY_RULES: [keyword: string, label: string][] = [
  ["hood", "Hoodies"],
  ["jacket", "Jackets"],
  ["quarter-zip", "Quarter-Zips"],
  ["crewneck", "Crewnecks & Sweatshirts"],
  ["sweatshirt", "Crewnecks & Sweatshirts"],
  ["shirt", "Shirts"],
];

export function categorize(garmentType: string): string {
  const lower = garmentType.toLowerCase();
  for (const [keyword, label] of CATEGORY_RULES) {
    if (lower.includes(keyword)) return label;
  }
  return "Other";
}
