"use client";

import { useQuery } from "@tanstack/react-query";
import { getScrapingJobs } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { CheckCircle2, XCircle, Clock, Loader2, ArrowLeft, Activity } from "lucide-react";
import Link from "next/link";

const STATUS_CONFIG = {
  completed: { icon: CheckCircle2, color: "text-green-400", bg: "bg-green-400/10 border-green-400/20" },
  failed:    { icon: XCircle,      color: "text-red-400",   bg: "bg-red-400/10 border-red-400/20" },
  running:   { icon: Loader2,      color: "text-yellow-400",bg: "bg-yellow-400/10 border-yellow-400/20" },
  pending:   { icon: Clock,        color: "text-slate-400", bg: "bg-slate-400/10 border-slate-400/20" },
};

export default function JobsPage() {
  const { data: jobs = [], isLoading, refetch } = useQuery({
    queryKey: ["scraping-jobs-page"],
    queryFn: () => getScrapingJobs(50),
    refetchInterval: 5000,
  });

  return (
    <div className="min-h-screen bg-surface text-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <Link href="/" className="text-slate-400 hover:text-slate-200 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <Activity className="w-5 h-5 text-brand-400" />
          <h1 className="text-xl font-semibold">Scraping Jobs</h1>
          <span className="text-xs bg-surface-3 text-slate-400 px-2 py-1 rounded">{jobs.length} total</span>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map(i => <div key={i} className="h-20 bg-surface-2 rounded-xl animate-pulse" />)}
          </div>
        ) : jobs.length === 0 ? (
          <div className="text-center py-16 text-slate-500">No scraping jobs yet. Trigger one from the dashboard.</div>
        ) : (
          <div className="space-y-3">
            {jobs.map(job => {
              const cfg = STATUS_CONFIG[job.status] || STATUS_CONFIG.pending;
              const Icon = cfg.icon;
              const duration = job.started_at && job.completed_at
                ? Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)
                : null;

              return (
                <div key={job.id} className={`flex items-center gap-4 p-4 rounded-xl border ${cfg.bg}`}>
                  <Icon className={`w-5 h-5 flex-shrink-0 ${cfg.color} ${job.status === "running" ? "animate-spin" : ""}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-200">Job #{job.id}</span>
                      <span className="text-xs bg-surface-3 text-slate-400 px-1.5 py-0.5 rounded">
                        {job.job_type.replace("_", " ")}
                      </span>
                      <span className={`text-xs font-medium ${cfg.color}`}>{job.status}</span>
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                      <span>Created {formatDate(job.created_at)}</span>
                      {job.completed_at && <span>Completed {formatDate(job.completed_at)}</span>}
                      {duration && <span>{duration}s</span>}
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    {job.total_records > 0 && (
                      <div className="flex items-center gap-1">
                        <span className="text-green-400">{job.success_records} ok</span>
                        {job.failed_records > 0 && <span className="text-red-400">/ {job.failed_records} fail</span>}
                        <span className="text-slate-500">/ {job.total_records} total</span>
                      </div>
                    )}
                    <span className="text-slate-600 capitalize">{job.triggered_by}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
