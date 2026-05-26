"use client";

import type { DashboardStats } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import { Pill, Store, BarChart3, Users, Clock, Star } from "lucide-react";

interface Props { stats: DashboardStats; }

export function StatsBar({ stats }: Props) {
  const cards = [
    { icon: Pill,     label: "Medications",   value: stats.total_medications,    color: "text-blue-400" },
    { icon: BarChart3,label: "Price Records",  value: stats.total_price_records.toLocaleString(),  color: "text-purple-400" },
    { icon: Store,    label: "Platforms",      value: stats.total_platforms,      color: "text-green-400" },
    { icon: Users,    label: "Vendors",        value: stats.total_vendors,        color: "text-orange-400" },
    { icon: Star,     label: "New Vendors",    value: stats.new_vendors_discovered, color: "text-yellow-400" },
    { icon: Clock,    label: "Last Updated",   value: formatDate(stats.last_scrape_at), color: "text-slate-400", wide: true },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map(({ icon: Icon, label, value, color, wide }) => (
        <div key={label} className={`glass-card px-4 py-3 ${wide ? "lg:col-span-1" : ""}`}>
          <div className="flex items-center gap-2 mb-1">
            <Icon className={`w-3.5 h-3.5 ${color}`} />
            <span className="text-xs text-slate-500">{label}</span>
          </div>
          <div className="text-lg font-semibold text-slate-100">{value}</div>
        </div>
      ))}
    </div>
  );
}
