"use client";

import { useCallback, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { autocomplete } from "@/lib/api";
import { CITY_OPTIONS } from "@/lib/utils";
import { Search, MapPin, X } from "lucide-react";

interface Props {
  query: string;
  city: string;
  onQueryChange: (q: string) => void;
  onCityChange: (city: string) => void;
}

export function SearchBar({ query, city, onQueryChange, onCityChange }: Props) {
  const [inputValue, setInputValue] = useState(query);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const { data: suggestions = [] } = useQuery({
    queryKey: ["autocomplete", inputValue],
    queryFn: () => autocomplete(inputValue),
    enabled: inputValue.length >= 2,
    staleTime: 10000,
  });

  useEffect(() => {
    const timer = setTimeout(() => {
      onQueryChange(inputValue);
    }, 300);
    return () => clearTimeout(timer);
  }, [inputValue, onQueryChange]);

  const handleSelect = (name: string) => {
    setInputValue(name);
    onQueryChange(name);
    setShowSuggestions(false);
  };

  return (
    <div className="flex flex-col sm:flex-row gap-3">
      {/* Search input */}
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={inputValue}
          onChange={e => { setInputValue(e.target.value); setShowSuggestions(true); }}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
          placeholder="Search medication (Mounjaro, Wegovy, Ozempic...)"
          className="w-full bg-surface-2 border border-slate-700 rounded-xl pl-10 pr-10 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/30 transition-all"
        />
        {inputValue && (
          <button
            onClick={() => { setInputValue(""); onQueryChange(""); }}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Autocomplete dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-1 bg-surface-2 border border-slate-700 rounded-xl shadow-2xl z-50 overflow-hidden animate-slide-up">
            {suggestions.map(s => (
              <button
                key={s.id}
                onMouseDown={() => handleSelect(s.name)}
                className="w-full text-left px-4 py-2.5 hover:bg-surface-3 transition-colors"
              >
                <div className="text-sm text-slate-100">{s.name}</div>
                {s.manufacturer && (
                  <div className="text-xs text-slate-500">{s.manufacturer}</div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* City select */}
      <div className="relative sm:w-52">
        <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
        <select
          value={city}
          onChange={e => onCityChange(e.target.value)}
          className="w-full bg-surface-2 border border-slate-700 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-100 focus:outline-none focus:border-brand-500 appearance-none cursor-pointer transition-all"
        >
          <option value="">All Cities</option>
          {CITY_OPTIONS.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>
    </div>
  );
}
