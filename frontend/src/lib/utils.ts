import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | null | undefined): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatDiscount(pct: number | null | undefined): string {
  if (pct == null || pct <= 0) return "";
  return `${pct.toFixed(1)}% off`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "Never";
  return new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function parseMedications(json: string | null): string[] {
  if (!json) return [];
  try { return JSON.parse(json); } catch { return []; }
}

export function getPlatformColor(slug: string): string {
  const colors: Record<string, string> = {
    pharmeasy: "#ff6b35",
    apollo: "#0070c0",
    tata1mg: "#e40046",
    netmeds: "#00a651",
    medplus: "#1a237e",
    truemeds: "#ff9800",
    mrmed: "#7c3aed",
    flipkart_health: "#2874f0",
    wellness_forever: "#006838",
    amazon_pharma: "#ff9900",
  };
  return colors[slug] || "#64748b";
}

export const CITY_OPTIONS = [
  "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata",
  "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Chandigarh", "Coimbatore",
  "Nagpur", "Indore", "Bhopal", "Surat", "Tirupati", "Amritsar",
  "Ludhiana", "Jabalpur", "Secunderabad", "Dharwad", "Parbhani", "Ranchi",
  "Dombivali", "Pan India",
];
