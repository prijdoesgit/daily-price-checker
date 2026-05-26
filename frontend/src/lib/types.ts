export interface Medication {
  id: number;
  name: string;
  canonical_name: string;
  generic_name: string | null;
  manufacturer: string | null;
  category: string | null;
  drug_type: "brand" | "generic";
  aliases: string | null;
  created_at: string;
  variants?: MedicationVariant[];
}

export interface MedicationVariant {
  id: number;
  medication_id: number;
  strength: string;
  strength_numeric: number | null;
  unit: string;
  form: string;
  pack_size: string | null;
  mrp: number | null;
  canonical_strength: string;
}

export interface Platform {
  id: number;
  name: string;
  slug: string;
  base_url: string;
  is_active: boolean;
  priority: number;
  last_scraped_at: string | null;
  scrape_success_rate: number;
}

export interface PriceRecord {
  id: number;
  variant_id: number;
  platform_id: number | null;
  platform_name: string | null;
  platform_slug: string | null;
  price: number | null;
  mrp: number | null;
  discount_pct: number | null;
  is_available: boolean;
  city: string | null;
  product_url: string | null;
  scraped_at: string;
}

export interface PriceComparison {
  variant_id: number;
  medication_name: string;
  strength: string;
  mrp: number | null;
  prices: PriceRecord[];
  cheapest: PriceRecord | null;
  cheapest_discount_pct: number | null;
  last_updated: string | null;
}

export interface Vendor {
  id: number;
  name: string;
  contact_name: string | null;
  phone: string | null;
  city: string | null;
  state: string | null;
  vendor_type: string;
  medications_handled: string | null;
  delivery_coverage: string | null;
  referred_by: string | null;
  is_verified: boolean;
  is_newly_discovered: boolean;
  created_at: string;
}

export interface DashboardStats {
  total_medications: number;
  total_variants: number;
  total_platforms: number;
  total_vendors: number;
  total_price_records: number;
  last_scrape_at: string | null;
  new_vendors_discovered: number;
}

export interface SearchResult {
  medication_id: number;
  medication_name: string;
  manufacturer: string | null;
  drug_type: string;
  variants: {
    id: number;
    strength: string;
    unit: string;
    form: string;
    mrp: number | null;
  }[];
  lowest_price: number | null;
  highest_price: number | null;
  cheapest_platform: string | null;
}

export interface Recommendation {
  variant_id: number;
  medication_name: string;
  strength: string;
  mrp: number | null;
  cheapest: PriceRecord | null;
  savings_vs_mrp: number | null;
  available_platforms: PriceRecord[];
  unavailable_platforms: PriceRecord[];
  city_vendors: {
    vendor_id: number;
    name: string;
    contact_name: string | null;
    phone: string | null;
    city: string | null;
    vendor_type: string;
    is_verified: boolean;
    referred_by: string | null;
  }[];
  generic_alternatives: {
    id: number;
    name: string;
    manufacturer: string | null;
    drug_type: string;
  }[];
  city: string | null;
}

export interface PriceMatrix {
  medication_id: number;
  platforms: { id: number; name: string; slug: string }[];
  matrix: {
    variant_id: number;
    strength: string;
    unit: string;
    form: string;
    mrp: number | null;
    prices: Record<string, { price: number; is_available: boolean; product_url: string | null; discount_pct: number | null } | null>;
    min_price: number | null;
    cheapest_platform: string | null;
  }[];
}

export interface ScrapingJob {
  id: number;
  job_type: string;
  platform_id: number | null;
  status: "pending" | "running" | "completed" | "failed";
  triggered_by: string;
  total_records: number;
  success_records: number;
  failed_records: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}
