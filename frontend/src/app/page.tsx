"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getDashboardStats, searchMedications } from "@/lib/api";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { SearchBar } from "@/components/dashboard/SearchBar";
import { StatsBar } from "@/components/dashboard/StatsBar";
import { MedicationCard } from "@/components/dashboard/MedicationCard";
import { VendorPanel } from "@/components/dashboard/VendorPanel";
import type { SearchResult } from "@/lib/types";

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCity, setSelectedCity] = useState("");
  const [activeTab, setActiveTab] = useState<"medications" | "vendors">("medications");

  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 60000,
  });

  const { data: results = [], isLoading } = useQuery({
    queryKey: ["search", searchQuery, selectedCity],
    queryFn: () => searchMedications(searchQuery || undefined, selectedCity || undefined),
    staleTime: 30000,
  });

  return (
    <div className="min-h-screen bg-surface text-slate-100">
      <DashboardHeader />

      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Stats bar */}
        {stats && <StatsBar stats={stats} />}

        {/* Search + Filters */}
        <SearchBar
          query={searchQuery}
          city={selectedCity}
          onQueryChange={setSearchQuery}
          onCityChange={setSelectedCity}
        />

        {/* Tab switch */}
        <div className="flex items-center gap-1 bg-surface-2 rounded-lg p-1 w-fit">
          {(["medications", "vendors"] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all capitalize ${
                activeTab === tab
                  ? "bg-brand-600 text-white shadow"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "medications" && (
          <div className="space-y-4">
            {isLoading ? (
              <LoadingSkeleton />
            ) : results.length === 0 ? (
              <EmptyState query={searchQuery} />
            ) : (
              results.map(med => (
                <MedicationCard
                  key={med.medication_id}
                  medication={med}
                  selectedCity={selectedCity}
                />
              ))
            )}
          </div>
        )}

        {activeTab === "vendors" && (
          <VendorPanel selectedCity={selectedCity} searchQuery={searchQuery} />
        )}
      </main>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map(i => (
        <div key={i} className="glass-card p-6 animate-pulse">
          <div className="h-6 bg-surface-3 rounded w-48 mb-4" />
          <div className="h-4 bg-surface-3 rounded w-32 mb-6" />
          <div className="grid grid-cols-5 gap-3">
            {[1, 2, 3, 4, 5].map(j => (
              <div key={j} className="h-16 bg-surface-3 rounded" />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ query }: { query: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <div className="text-6xl mb-4">💊</div>
      <h3 className="text-xl font-semibold text-slate-200 mb-2">
        {query ? `No results for "${query}"` : "Search for a medication"}
      </h3>
      <p className="text-slate-400 max-w-md">
        {query
          ? "Try a different name or generic name. We track Wegovy, Ozempic, Mounjaro, Noveltreat, Obeda and more."
          : "Start typing a medication name above to compare prices across all Indian pharmacy platforms."}
      </p>
    </div>
  );
}
