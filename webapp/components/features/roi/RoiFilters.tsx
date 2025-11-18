"use client";

import { useEffect, useMemo, useState, useId } from "react";

import { FilterBar } from "@/components/data";
import { Checkbox, Input } from "@/components/ui";

import { ROI_TABLE_DEFAULTS, type RoiTableFilters } from "./tableState";

type RoiFiltersProps = {
  filters: RoiTableFilters;
  onApply: (filters: RoiTableFilters) => void;
  onReset: () => void;
};

const normalizeFilters = (filters: RoiTableFilters): RoiTableFilters => ({
  roiMin: filters.roiMin ?? 0,
  vendor: filters.vendor ?? "",
  category: filters.category ?? "",
  search: filters.search ?? "",
  observeOnly: Boolean(filters.observeOnly),
});

const areFiltersEqual = (a: RoiTableFilters, b: RoiTableFilters): boolean =>
  JSON.stringify(normalizeFilters(a)) === JSON.stringify(normalizeFilters(b));

export function RoiFilters({ filters, onApply, onReset }: RoiFiltersProps) {
  const [draft, setDraft] = useState<RoiTableFilters>(normalizeFilters(filters));
  const searchId = useId();
  const vendorId = useId();
  const categoryId = useId();
  const roiId = useId();
  const observeId = useId();

  useEffect(() => {
    setDraft(normalizeFilters(filters));
  }, [filters]);

  const isDirty = useMemo(() => !areFiltersEqual(draft, filters), [draft, filters]);

  const handleApply = () => {
    onApply(normalizeFilters(draft));
  };

  const handleReset = () => {
    setDraft(normalizeFilters(ROI_TABLE_DEFAULTS.filters ?? {}));
    onReset();
  };

  return (
    <FilterBar onApply={handleApply} onReset={handleReset} isDirty={isDirty}>
      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground" htmlFor={searchId}>
          Search
        </label>
        <Input
          id={searchId}
          placeholder="Find ASIN or title"
          value={draft.search ?? ""}
          onChange={(event) =>
            setDraft((current) => ({ ...current, search: event.target.value }))
          }
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground" htmlFor={vendorId}>
          Vendor ID
        </label>
        <Input
          id={vendorId}
          placeholder="Vendor"
          value={draft.vendor ?? ""}
          onChange={(event) =>
            setDraft((current) => ({ ...current, vendor: event.target.value }))
          }
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground" htmlFor={categoryId}>
          Category
        </label>
        <Input
          id={categoryId}
          placeholder="Category"
          value={draft.category ?? ""}
          onChange={(event) =>
            setDraft((current) => ({ ...current, category: event.target.value }))
          }
        />
      </div>

      <div className="flex flex-col gap-2">
        <label className="text-xs font-semibold uppercase text-muted-foreground" htmlFor={roiId}>
          ROI ≥ (%)
        </label>
        <Input
          id={roiId}
          type="number"
          min={0}
          step={1}
          value={draft.roiMin ?? 0}
          onChange={(event) =>
            setDraft((current) => ({
              ...current,
              roiMin: event.target.value === "" ? undefined : Number(event.target.value),
            }))
          }
        />
      </div>

      <label className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground" htmlFor={observeId}>
        <Checkbox
          id={observeId}
          checked={Boolean(draft.observeOnly)}
          onChange={(event) =>
            setDraft((current) => ({ ...current, observeOnly: event.target.checked }))
          }
        />
        <span className="text-sm font-normal normal-case text-foreground">Observe only</span>
      </label>
    </FilterBar>
  );
}
