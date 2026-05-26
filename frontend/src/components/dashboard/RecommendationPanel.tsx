"use client";

import { formatCurrency, formatDate, getPlatformColor } from "@/lib/utils";
import { TrendingDown, MapPin, Phone, CheckCircle, ExternalLink, BarChart2, Users } from "lucide-react";
import type { Recommendation } from "@/lib/types";
import { PriceHistoryChart } from "./PriceHistoryChart";

interface Props {
  recommendation: Recommendation;
  showChart: boolean;
  onToggleChart: () => void;
  selectedVariantId: number | null;
}

export function RecommendationPanel({ recommendation, showChart, onToggleChart, selectedVariantId }: Props) {
  const { cheapest, savings_vs_mrp, available_platforms, city_vendors, generic_alternatives, city } = recommendation;

  return (
    <div className="border-t border-slate-800 bg-surface-2/30 p-5 space-y-6">
      {/* Cheapest Recommendation Banner */}
      {cheapest && (
        <div className="flex items-center justify-between bg-green-500/10 border border-green-500/20 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center">
              <TrendingDown className="w-4 h-4 text-green-400" />
            </div>
            <div>
              <p className="text-xs text-green-500 font-medium uppercase tracking-wide">Best Price Found</p>
              <p className="text-lg font-bold text-green-400">{formatCurrency(cheapest.price)}</p>
              <p className="text-xs text-slate-400">on {cheapest.platform_name}</p>
            </div>
          </div>
          <div className="text-right">
            {savings_vs_mrp && savings_vs_mrp > 0 && (
              <div>
                <p className="text-xs text-slate-500">Save vs MRP</p>
                <p className="text-base font-bold text-green-400">− {formatCurrency(savings_vs_mrp)}</p>
              </div>
            )}
            {cheapest.product_url && (
              <a
                href={cheapest.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 mt-2 text-xs text-brand-400 hover:text-brand-300"
              >
                Buy now <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        </div>
      )}

      {/* All Platform Prices */}
      <div>
        <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          All Platforms ({available_platforms.length} available)
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-2">
          {available_platforms.map((p, idx) => {
            const isBest = idx === 0;
            return (
              <a
                key={p.platform_id}
                href={p.product_url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className={`relative p-3 rounded-lg border transition-all group cursor-pointer ${
                  isBest
                    ? "price-cheapest border-green-500/30"
                    : "bg-surface-3/50 border-slate-700 hover:border-slate-600"
                }`}
              >
                {isBest && (
                  <span className="absolute -top-2 left-2 text-[10px] bg-green-500 text-white px-1.5 py-0.5 rounded font-semibold">
                    BEST
                  </span>
                )}
                <div className="flex items-center justify-between mb-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: getPlatformColor(p.platform_slug || "") }}
                  />
                  <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-slate-400" />
                </div>
                <p className="text-xs text-slate-400 mb-1 truncate">{p.platform_name}</p>
                <p className={`text-sm font-bold font-mono ${isBest ? "text-green-400" : "text-slate-200"}`}>
                  {formatCurrency(p.price)}
                </p>
                {p.discount_pct && p.discount_pct > 0 && (
                  <p className="text-[10px] text-slate-500 mt-0.5">{p.discount_pct?.toFixed(1)}% off</p>
                )}
                <p className="text-[10px] text-slate-600 mt-1">{formatDate(p.scraped_at)}</p>
              </a>
            );
          })}
        </div>
      </div>

      {/* Price history toggle */}
      {selectedVariantId && (
        <div>
          <button
            onClick={onToggleChart}
            className="flex items-center gap-2 text-xs text-brand-400 hover:text-brand-300 transition-colors"
          >
            <BarChart2 className="w-3.5 h-3.5" />
            {showChart ? "Hide" : "Show"} Price History
          </button>
          {showChart && <PriceHistoryChart variantId={selectedVariantId} />}
        </div>
      )}

      {/* City vendors */}
      {city_vendors.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5" />
            Local Vendors{city ? ` in ${city}` : ""}
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {city_vendors.map(v => (
              <div key={v.vendor_id} className="bg-surface-3/50 border border-slate-700 rounded-lg p-3">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <p className="text-sm font-medium text-slate-200">{v.name}</p>
                    {v.contact_name && <p className="text-xs text-slate-500">{v.contact_name}</p>}
                  </div>
                  {v.is_verified && (
                    <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0 mt-0.5" />
                  )}
                </div>
                <div className="space-y-1">
                  {v.city && (
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <MapPin className="w-3 h-3" />
                      {v.city}
                    </div>
                  )}
                  {v.phone && (
                    <div className="flex items-center gap-1.5 text-xs">
                      <Phone className="w-3 h-3 text-slate-400" />
                      <a href={`tel:${v.phone}`} className="text-brand-400 hover:underline">{v.phone}</a>
                    </div>
                  )}
                  {v.referred_by && (
                    <p className="text-xs text-slate-500 italic">via {v.referred_by}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generic alternatives */}
      {generic_alternatives.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Generic / Equivalent Options
          </h4>
          <div className="flex flex-wrap gap-2">
            {generic_alternatives.map(alt => (
              <div
                key={alt.id}
                className="flex items-center gap-2 bg-surface-3/50 border border-slate-700 rounded-lg px-3 py-2"
              >
                <span className="text-sm text-slate-200">{alt.name}</span>
                <span className="text-xs text-slate-500">{alt.manufacturer}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded ${
                  alt.drug_type === "generic" ? "bg-green-500/10 text-green-400" : "bg-blue-500/10 text-blue-400"
                }`}>
                  {alt.drug_type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
