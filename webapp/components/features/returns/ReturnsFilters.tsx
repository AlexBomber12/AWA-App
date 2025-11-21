"use client";

import { useEffect, useMemo, useState } from "react";

import { FilterBar } from "@/components/data";
import { Input } from "@/components/ui";

import { RETURNS_TABLE_DEFAULTS, type ReturnsTableFilters } from "@/lib/tableState/returns";

type ReturnsFiltersProps = {
  filters: ReturnsTableFilters;
  onApply: (filters: ReturnsTableFilters) => void;
  onReset: () => void;
};

type NormalizedFilters = {
  dateFrom: string;
  dateTo: string;
  vendor: string;
  asin: string;
};

const normalizeFilters = (filters: ReturnsTableFilters): NormalizedFilters => ({
  dateFrom: filters.dateFrom ?? "",
  dateTo: filters.dateTo ?? "",
  vendor: filters.vendor ?? "",
  asin: filters.asin ?? "",
});

const buildPayload = (filters: NormalizedFilters): ReturnsTableFilters => ({
  dateFrom: filters.dateFrom.trim() ? filters.dateFrom : undefined,
  dateTo: filters.dateTo.trim() ? filters.dateTo : undefined,
  vendor: filters.vendor.trim() ? filters.vendor : undefined,
  asin: filters.asin.trim() ? filters.asin : undefined,
});

const areFiltersEqual = (a: NormalizedFilters, b: NormalizedFilters) =>
  JSON.stringify(a) === JSON.stringify(b);

export function ReturnsFilters({ filters, onApply, onReset }: ReturnsFiltersProps) {
  const [draft, setDraft] = useState<NormalizedFilters>(normalizeFilters(filters));

  useEffect(() => {
    setDraft(normalizeFilters(filters));
  }, [filters]);

  const isDirty = useMemo(() => !areFiltersEqual(draft, normalizeFilters(filters)), [draft, filters]);

  const handleApply = () => {
    onApply(buildPayload(draft));
  };

  const handleReset = () => {
    setDraft(normalizeFilters(RETURNS_TABLE_DEFAULTS.filters ?? {}));
    onReset();
  };

  return (
    <FilterBar onApply={handleApply} onReset={handleReset} isDirty={isDirty}>
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground">From</label>
        <Input
          type="date"
          value={draft.dateFrom}
          onChange={(event) => setDraft((current) => ({ ...current, dateFrom: event.target.value }))}
          max={draft.dateTo || undefined}
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground">To</label>
        <Input
          type="date"
          value={draft.dateTo}
          onChange={(event) => setDraft((current) => ({ ...current, dateTo: event.target.value }))}
          min={draft.dateFrom || undefined}
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground">Vendor</label>
        <Input
          placeholder="Vendor ID"
          value={draft.vendor}
          onChange={(event) => setDraft((current) => ({ ...current, vendor: event.target.value }))}
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground">ASIN</label>
        <Input
          placeholder="ASIN"
          value={draft.asin}
          onChange={(event) => setDraft((current) => ({ ...current, asin: event.target.value }))}
        />
      </div>
    </FilterBar>
  );
}
