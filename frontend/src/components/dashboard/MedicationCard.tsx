"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getPriceMatrix, getRecommendations } from "@/lib/api";
import { formatCurrency, formatDiscount, formatDate, getPlatformColor } from "@/lib/utils";
import { ChevronDown, ChevronUp, ExternalLink, TrendingDown, Zap, MapPin } from "lucide-react";
import type { SearchResult } from "@/lib/types";
import { PriceHistoryChart } from "./PriceHistoryChart";
import { RecommendationPanel } from "./RecommendationPanel";

interface Props {
  medication: SearchResult;
  selectedCity: string;
}

export function MedicationCard({ medication, selectedCity }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [selectedVariantId, setSelectedVariantId] = useState<number | null>(null);
  const [showChart, setShowChart] = useState(false);

  const { data: matrix, isLoading } = useQuery({
    queryKey: ["price-matrix", medication.medication_id],
    queryFn: () => getPriceMatrix(medication.medication_id),
    enabled: expanded,
    staleTime: 60000,
  });

  const activeVariant = selectedVariantId || medication.variants[0]?.id;
  const { data: recommendation } = useQuery({
    queryKey: ["recommendation", medication.medication_id, activeVariant, selectedCity],
    queryFn: () => getRecommendations(medication.medication_id, activeVariant!, selectedCity || undefined),
    enabled: expanded && !!activeVariant,
    staleTime: 60000,
  });

  const drugTypeColor = medication.drug_type === "brand" ? "text-blue-400 bg-blue-400/10" : "text-green-400 bg-green-400/10";

  return (
    <div className="glass-card overflow-hidden transition-all duration-200">
      {/* Card header — always visible */}
      <div
        className="flex items-center justify-between p-5 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand-600/20 to-purple-600/20 border border-brand-500/20 flex items-center justify-center">
            <span className="text-lg">💊</span>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-white">{medication.medication_name}</h3>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${drugTypeColor}`}>
                {medication.drug_type}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              {medication.manufacturer} · {medication.variants.length} strengths
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Price range */}
          <div className="hidden md:block text-right">
            {medication.lowest_price && (
              <div className="flex items-center gap-1.5 justify-end">
                <TrendingDown className="w-3.5 h-3.5 text-green-400" />
                <span className="text-sm font-semibold text-green-400">{formatCurrency(medication.lowest_price)}</span>
              </div>
            )}
            {medication.cheapest_platform && (
              <p className="text-xs text-slate-500">cheapest on {medication.cheapest_platform}</p>
            )}
          </div>

          {/* Variant pills */}
          <div className="hidden lg:flex flex-wrap gap-1.5 max-w-xs">
            {medication.variants.slice(0, 5).map(v => (
              <span key={v.id} className="text-xs bg-surface-3 text-slate-300 px-2 py-0.5 rounded-md">
                {v.strength}
              </span>
            ))}
            {medication.variants.length > 5 && (
              <span className="text-xs text-slate-500">+{medication.variants.length - 5}</span>
            )}
          </div>

          <div className="text-slate-400">
            {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-slate-800 animate-fade-in">
          {/* Strength selector */}
          <div className="flex items-center gap-2 px-5 py-3 bg-surface-2/50 overflow-x-auto">
            <span className="text-xs text-slate-500 whitespace-nowrap">Strength:</span>
            {medication.variants.map(v => (
              <button
                key={v.id}
                onClick={() => setSelectedVariantId(v.id)}
                className={`px-3 py-1 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                  (selectedVariantId || medication.variants[0]?.id) === v.id
                    ? "bg-brand-600 text-white"
                    : "bg-surface-3 text-slate-400 hover:text-white"
                }`}
              >
                {v.strength}
                {v.mrp && <span className="ml-1 text-slate-500">· {formatCurrency(v.mrp)}</span>}
              </button>
            ))}
          </div>

          {/* Price matrix */}
          {isLoading ? (
            <div className="p-6 grid grid-cols-5 gap-3">
              {[...Array(10)].map((_, i) => <div key={i} className="h-16 bg-surface-3 rounded animate-pulse" />)}
            </div>
          ) : matrix ? (
            <PriceMatrixTable
              matrix={matrix}
              selectedVariantId={activeVariant}
            />
          ) : null}

          {/* Recommendations */}
          {recommendation && (
            <RecommendationPanel
              recommendation={recommendation}
              showChart={showChart}
              onToggleChart={() => setShowChart(s => !s)}
              selectedVariantId={activeVariant}
            />
          )}
        </div>
      )}
    </div>
  );
}


function PriceMatrixTable({ matrix, selectedVariantId }: { matrix: any; selectedVariantId: number | null }) {
  const platforms = matrix.platforms;
  const rows = selectedVariantId
    ? matrix.matrix.filter((r: any) => r.variant_id === selectedVariantId)
    : matrix.matrix;

  if (!rows.length) return null;

  return (
    <div className="overflow-x-auto p-5">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left text-xs text-slate-500 font-medium pb-3 pr-4 whitespace-nowrap">Strength</th>
            <th className="text-right text-xs text-slate-500 font-medium pb-3 pr-4 whitespace-nowrap">MRP</th>
            {platforms.map((p: any) => (
              <th key={p.id} className="text-right text-xs pb-3 px-2 whitespace-nowrap">
                <span className="text-slate-400 font-medium">{p.name}</span>
              </th>
            ))}
            <th className="text-right text-xs text-slate-500 font-medium pb-3 pl-4 whitespace-nowrap">Best Price</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {rows.map((row: any) => {
            const prices = platforms.map((p: any) => row.prices[p.slug]);
            const minPrice = row.min_price;

            return (
              <tr key={row.variant_id} className="hover:bg-surface-2/30 transition-colors">
                <td className="py-3 pr-4 text-slate-200 font-medium">{row.strength}</td>
                <td className="py-3 pr-4 text-right text-slate-400 font-mono">{formatCurrency(row.mrp)}</td>
                {platforms.map((p: any) => {
                  const priceData = row.prices[p.slug];
                  const price = priceData?.price;
                  const isCheapest = price && price === minPrice;
                  const isUnavail = !priceData || !priceData.is_available;

                  return (
                    <td key={p.id} className="py-3 px-2 text-right">
                      {isUnavail ? (
                        <span className="text-slate-600 text-xs">—</span>
                      ) : (
                        <div className="inline-flex flex-col items-end">
                          <span className={`font-mono text-sm font-medium ${isCheapest ? "text-green-400" : "text-slate-300"}`}>
                            {formatCurrency(price)}
                          </span>
                          {isCheapest && (
                            <span className="text-[10px] text-green-500 font-medium">BEST</span>
                          )}
                          {(priceData.discount_pct ?? 0) > 0 && (
                            <span className="text-[10px] text-slate-500">{formatDiscount(priceData.discount_pct)}</span>
                          )}
                        </div>
                      )}
                    </td>
                  );
                })}
                <td className="py-3 pl-4 text-right">
                  {row.min_price ? (
                    <div className="inline-flex flex-col items-end">
                      <span className="font-mono text-sm font-bold text-green-400">{formatCurrency(row.min_price)}</span>
                      {row.cheapest_platform && (
                        <span className="text-[10px] text-slate-500">{row.cheapest_platform}</span>
                      )}
                    </div>
                  ) : <span className="text-slate-600">—</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
