"use client";

import { useQuery } from "@tanstack/react-query";
import { getVendors } from "@/lib/api";
import { formatDate, parseMedications } from "@/lib/utils";
import { Phone, MapPin, CheckCircle, Sparkles, Users } from "lucide-react";

interface Props {
  selectedCity: string;
  searchQuery: string;
}

const VENDOR_TYPE_LABELS: Record<string, string> = {
  distributor: "Distributor",
  wholesaler: "Wholesaler",
  online_platform: "Online Platform",
  regional: "Regional",
  b2b: "B2B",
};

const VENDOR_TYPE_COLORS: Record<string, string> = {
  distributor: "text-blue-400 bg-blue-400/10",
  wholesaler: "text-purple-400 bg-purple-400/10",
  online_platform: "text-green-400 bg-green-400/10",
  regional: "text-orange-400 bg-orange-400/10",
  b2b: "text-yellow-400 bg-yellow-400/10",
};

export function VendorPanel({ selectedCity, searchQuery }: Props) {
  const { data: vendors = [], isLoading } = useQuery({
    queryKey: ["vendors", selectedCity, searchQuery],
    queryFn: () => getVendors({
      city: selectedCity || undefined,
      medication: searchQuery || undefined,
    }),
    staleTime: 60000,
  });

  const newVendors = vendors.filter(v => v.is_newly_discovered);
  const regularVendors = vendors.filter(v => !v.is_newly_discovered);

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="glass-card p-4 h-36 animate-pulse">
            <div className="h-4 bg-surface-3 rounded w-3/4 mb-3" />
            <div className="h-3 bg-surface-3 rounded w-1/2 mb-2" />
            <div className="h-3 bg-surface-3 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Newly discovered */}
      {newVendors.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-yellow-400" />
            <h3 className="text-sm font-semibold text-yellow-400">
              Newly Discovered Vendors ({newVendors.length})
            </h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {newVendors.map(v => <VendorCard key={v.id} vendor={v} isNew />)}
          </div>
        </div>
      )}

      {/* Regular vendors */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-4 h-4 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-300">
            All Vendors{selectedCity ? ` in ${selectedCity}` : ""} ({regularVendors.length})
          </h3>
        </div>

        {regularVendors.length === 0 ? (
          <div className="text-center py-12 text-slate-500">
            <Users className="w-8 h-8 mx-auto mb-3 opacity-40" />
            <p>No vendors found{selectedCity ? ` in ${selectedCity}` : ""}</p>
            {selectedCity && <p className="text-xs mt-1">Try clearing the city filter</p>}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {regularVendors.map(v => <VendorCard key={v.id} vendor={v} />)}
          </div>
        )}
      </div>
    </div>
  );
}

function VendorCard({ vendor, isNew = false }: { vendor: any; isNew?: boolean }) {
  const medications = parseMedications(vendor.medications_handled);
  const coverage = parseMedications(vendor.delivery_coverage);
  const typeClass = VENDOR_TYPE_COLORS[vendor.vendor_type] || "text-slate-400 bg-slate-400/10";

  return (
    <div className={`glass-card p-4 transition-all hover:border-slate-600 ${isNew ? "border-yellow-500/30" : ""}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <h4 className="text-sm font-semibold text-slate-100 truncate">{vendor.name}</h4>
            {vendor.is_verified && <CheckCircle className="w-3.5 h-3.5 text-green-400 flex-shrink-0" />}
          </div>
          {vendor.contact_name && (
            <p className="text-xs text-slate-500 truncate">{vendor.contact_name}</p>
          )}
        </div>
        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium whitespace-nowrap ml-2 ${typeClass}`}>
          {VENDOR_TYPE_LABELS[vendor.vendor_type] || vendor.vendor_type}
        </span>
      </div>

      {/* Contact info */}
      <div className="space-y-1.5 mb-3">
        {vendor.city && (
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <MapPin className="w-3 h-3 flex-shrink-0" />
            <span>{vendor.city}</span>
          </div>
        )}
        {vendor.phone && (
          <div className="flex items-center gap-1.5">
            <Phone className="w-3 h-3 text-slate-400 flex-shrink-0" />
            <a href={`tel:${vendor.phone}`} className="text-xs text-brand-400 hover:underline">
              {vendor.phone}
            </a>
          </div>
        )}
      </div>

      {/* Medications */}
      {medications.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {medications.slice(0, 3).map(med => (
            <span key={med} className="text-[10px] bg-surface-3 text-slate-400 px-1.5 py-0.5 rounded">
              {med}
            </span>
          ))}
          {medications.length > 3 && (
            <span className="text-[10px] text-slate-600">+{medications.length - 3}</span>
          )}
        </div>
      )}

      {/* Coverage */}
      {coverage.length > 0 && (
        <p className="text-[10px] text-slate-500">
          Ships to: {coverage.slice(0, 3).join(", ")}{coverage.length > 3 ? "…" : ""}
        </p>
      )}

      {/* Referred by */}
      {vendor.referred_by && (
        <p className="text-[10px] text-slate-600 mt-1.5 italic truncate" title={vendor.referred_by}>
          via {vendor.referred_by}
        </p>
      )}
    </div>
  );
}
