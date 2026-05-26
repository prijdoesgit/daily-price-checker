"use client";

import { useQuery } from "@tanstack/react-query";
import { getPriceHistory, getPlatforms } from "@/lib/api";
import { formatCurrency, getPlatformColor } from "@/lib/utils";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import { format } from "date-fns";

interface Props {
  variantId: number;
  days?: number;
}

export function PriceHistoryChart({ variantId, days = 30 }: Props) {
  const { data: history = [], isLoading } = useQuery({
    queryKey: ["price-history", variantId, days],
    queryFn: () => getPriceHistory(variantId, undefined, days),
    enabled: !!variantId,
  });

  const { data: platforms = [] } = useQuery({
    queryKey: ["platforms"],
    queryFn: getPlatforms,
    staleTime: Infinity,
  });

  if (isLoading) {
    return <div className="h-48 bg-surface-3 rounded-lg animate-pulse mt-3" />;
  }

  if (!history.length) {
    return (
      <div className="h-32 flex items-center justify-center text-slate-500 text-sm mt-3">
        No price history available yet
      </div>
    );
  }

  // Pivot to {date: {platform: price}} for recharts
  const pivotMap = new Map<string, Record<string, string | number>>();
  for (const h of history) {
    const dateKey = format(new Date(h.date), "dd MMM");
    if (!pivotMap.has(dateKey)) pivotMap.set(dateKey, { date: dateKey });
    const entry = pivotMap.get(dateKey)!;
    entry[h.platform] = h.price;
  }
  const chartData = Array.from(pivotMap.values());
  const platformsInData: string[] = Array.from(new Set<string>(history.map((h: any) => h.platform as string)));

  return (
    <div className="mt-3 bg-surface-3/30 rounded-xl p-4">
      <p className="text-xs text-slate-400 mb-3">Price trend — last {days} days</p>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="date" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={v => `₹${(v / 1000).toFixed(0)}k`}
            width={45}
          />
          <Tooltip
            contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
            labelStyle={{ color: "#94a3b8", fontSize: 11 }}
            formatter={(value: number) => [formatCurrency(value), ""]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "#64748b" }}
            iconType="circle"
            iconSize={8}
          />
          {platformsInData.map((platform: string) => (
            <Line
              key={platform}
              type="monotone"
              dataKey={platform}
              stroke={getPlatformColor(platform.toLowerCase().replace(/\s/g, "_"))}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
