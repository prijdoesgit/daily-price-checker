import axios from "axios";
import type {
  Medication, MedicationVariant, Platform, PriceRecord, PriceComparison,
  Vendor, DashboardStats, SearchResult, Recommendation, PriceMatrix, ScrapingJob
} from "./types";

const api = axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api`,
  timeout: 30000,
});

// ── Medications ──────────────────────────────────────────────────────────────

export const getMedications = (params?: { search?: string; drug_type?: string }) =>
  api.get<Medication[]>("/medications/", { params }).then(r => r.data);

export const getMedication = (id: number) =>
  api.get<Medication>(`/medications/${id}`).then(r => r.data);

export const getMedicationVariants = (id: number) =>
  api.get<MedicationVariant[]>(`/medications/${id}/variants`).then(r => r.data);

export const autocomplete = (q: string) =>
  api.get<{ id: number; name: string; canonical_name: string; manufacturer: string }[]>(
    "/medications/search/autocomplete", { params: { q } }
  ).then(r => r.data);

// ── Prices ───────────────────────────────────────────────────────────────────

export const getPrices = (variantId: number, city?: string) =>
  api.get<PriceRecord[]>(`/prices/variant/${variantId}`, { params: { city } }).then(r => r.data);

export const comparePrices = (variantId: number, city?: string) =>
  api.get<PriceComparison>(`/prices/compare/${variantId}`, { params: { city } }).then(r => r.data);

export const getPriceHistory = (variantId: number, platformId?: number, days = 30) =>
  api.get(`/prices/history/${variantId}`, { params: { platform_id: platformId, days } }).then(r => r.data);

// ── Vendors ──────────────────────────────────────────────────────────────────

export const getVendors = (params?: { city?: string; medication?: string; vendor_type?: string }) =>
  api.get<Vendor[]>("/vendors/", { params }).then(r => r.data);

export const getPlatforms = () =>
  api.get<Platform[]>("/vendors/platforms").then(r => r.data);

export const getCities = () =>
  api.get<string[]>("/vendors/cities/list").then(r => r.data);

// ── Dashboard ─────────────────────────────────────────────────────────────────

export const getDashboardStats = () =>
  api.get<DashboardStats>("/dashboard/stats").then(r => r.data);

export const searchMedications = (q?: string, city?: string) =>
  api.get<SearchResult[]>("/dashboard/search", { params: { q, city } }).then(r => r.data);

export const getPriceMatrix = (medicationId: number) =>
  api.get<PriceMatrix>(`/dashboard/price-matrix/${medicationId}`).then(r => r.data);

export const getRecommendations = (medicationId: number, variantId: number, city?: string) =>
  api.get<Recommendation>(`/dashboard/recommendations/${medicationId}/${variantId}`, { params: { city } }).then(r => r.data);

// ── Scraping ──────────────────────────────────────────────────────────────────

export const triggerFullScrape = () =>
  api.post<{ job_id: number; status: string }>("/scraping/trigger/full").then(r => r.data);

export const triggerPlatformScrape = (platformId: number) =>
  api.post<{ job_id: number; status: string }>(`/scraping/trigger/platform/${platformId}`).then(r => r.data);

export const getScrapingJobs = (limit = 20) =>
  api.get<ScrapingJob[]>("/scraping/jobs", { params: { limit } }).then(r => r.data);

export const getJob = (jobId: number) =>
  api.get<ScrapingJob>(`/scraping/jobs/${jobId}`).then(r => r.data);
