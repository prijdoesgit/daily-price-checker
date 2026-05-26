"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { triggerFullScrape, getScrapingJobs } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { RefreshCw, Activity, Zap } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

export function DashboardHeader() {
  const queryClient = useQueryClient();
  const [scrapeMsg, setScrapeMsg] = useState("");

  const { data: jobs } = useQuery({
    queryKey: ["scraping-jobs"],
    queryFn: () => getScrapingJobs(5),
    refetchInterval: 10000,
  });

  const latestJob = jobs?.[0];
  const isRunning = latestJob?.status === "running" || latestJob?.status === "pending";

  const mutation = useMutation({
    mutationFn: triggerFullScrape,
    onSuccess: (data) => {
      setScrapeMsg(`Job #${data.job_id} queued`);
      queryClient.invalidateQueries({ queryKey: ["scraping-jobs"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      setTimeout(() => setScrapeMsg(""), 5000);
    },
    onError: () => setScrapeMsg("Failed to trigger scrape"),
  });

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-surface/95 backdrop-blur-md">
      <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo + title */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
              <span className="text-white text-xs font-bold">Rx</span>
            </div>
            <div>
              <h1 className="text-base font-semibold text-white leading-none">MedPrice Intelligence</h1>
              <p className="text-xs text-slate-500 mt-0.5">India Pharmacy Price Tracker</p>
            </div>
          </div>

          {/* Right controls */}
          <div className="flex items-center gap-3">
            {/* Latest scrape status */}
            {latestJob && (
              <div className="hidden md:flex items-center gap-2 text-xs text-slate-400">
                <div className={`w-2 h-2 rounded-full ${isRunning ? "bg-yellow-400 animate-pulse" : "bg-green-400"}`} />
                <span>
                  {isRunning ? "Scraping…" : `Updated ${formatDate(latestJob.completed_at)}`}
                </span>
              </div>
            )}

            {scrapeMsg && (
              <span className="text-xs text-green-400 animate-fade-in">{scrapeMsg}</span>
            )}

            {/* Refresh button */}
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || isRunning}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                mutation.isPending || isRunning
                  ? "bg-surface-3 text-slate-500 cursor-not-allowed"
                  : "bg-brand-600 hover:bg-brand-700 text-white shadow-lg hover:shadow-brand-600/25"
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${(mutation.isPending || isRunning) ? "animate-spin" : ""}`} />
              <span>{isRunning ? "Refreshing…" : "Refresh Prices"}</span>
            </button>

            <a
              href="/jobs"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-slate-400 hover:text-white hover:bg-surface-2 transition-all"
            >
              <Activity className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Jobs</span>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}
