"use client";

import { type ReactNode, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/data";
import { Button } from "@/components/ui";
import { roiClient } from "@/lib/api/roiClient";
import { useTableState } from "@/lib/tableState";
import {
  ROI_TABLE_DEFAULTS,
  parseRoiSearchParams,
  serializeRoiSearchParams,
  type RoiSort,
  type RoiTableFilters,
} from "@/lib/tableState/roi";

import { RoiBulkApproveDialog } from "./RoiBulkApproveDialog";
import { RoiFilters } from "./RoiFilters";
import { RoiTable } from "./RoiTable";

type RoiTableContainerProps = {
  canApprove: boolean;
  onActionsChange?: (node: ReactNode | null) => void;
};

// Canonical large-table pattern (filters + URL + virtualization)
export function RoiTableContainer({ canApprove, onActionsChange }: RoiTableContainerProps) {
  const queryClient = useQueryClient();
  const [selectedAsins, setSelectedAsins] = useState<Set<string>>(new Set());
  const [isBulkDialogOpen, setBulkDialogOpen] = useState(false);

  const { state, setPage, setPageSize, setSort, setFilters, resetFilters } = useTableState<
    RoiSort,
    RoiTableFilters
  >({
    defaults: ROI_TABLE_DEFAULTS,
    parseFromSearchParams: parseRoiSearchParams,
    serializeToSearchParams: serializeRoiSearchParams,
  });

  const appliedFilters = state.filters ?? ROI_TABLE_DEFAULTS.filters ?? {};

  const {
    data,
    isPending,
    isRefetching,
    error,
    refetch,
  } = roiClient.useRoiQuery(
    {
      page: state.page,
      pageSize: state.pageSize,
      sort: state.sort ?? ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc",
      filters: appliedFilters,
    },
    { placeholderData: (previousData) => previousData }
  );

  const handleSelectRow = (asin: string, checked: boolean) => {
    setSelectedAsins((current) => {
      const next = new Set(current);
      if (checked) {
        next.add(asin);
      } else {
        next.delete(asin);
      }
      return next;
    });
  };

  const handleSelectVisibleRows = (asins: string[], checked: boolean) => {
    setSelectedAsins((current) => {
      const next = new Set(current);
      asins.forEach((asin) => {
        if (checked) {
          next.add(asin);
        } else {
          next.delete(asin);
        }
      });
      return next;
    });
  };

  const clearSelection = () => setSelectedAsins(new Set());

  const bulkApproveAction = useMemo(() => {
    if (!canApprove) {
      return null;
    }
    const selectedCount = selectedAsins.size;
    return (
      <Button
        size="sm"
        onClick={() => setBulkDialogOpen(true)}
        disabled={selectedCount === 0}
      >
        Bulk approve{selectedCount ? ` (${selectedCount})` : ""}
      </Button>
    );
  }, [canApprove, selectedAsins.size]);

  useEffect(() => {
    if (!onActionsChange) {
      return;
    }
    onActionsChange(bulkApproveAction);
    return () => onActionsChange(null);
  }, [bulkApproveAction, onActionsChange]);

  const handleFiltersApply = (filters: RoiTableFilters) => {
    setFilters(filters);
  };

  const handleBulkApproveSuccess = async () => {
    clearSelection();
    setBulkDialogOpen(false);
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["roi"] }),
      refetch(),
    ]);
  };

  return (
    <div className="space-y-6">
      <RoiFilters
        filters={appliedFilters}
        onApply={handleFiltersApply}
        onReset={resetFilters}
      />

      {error ? (
        <ErrorState
          title="Unable to load ROI rows"
          error={error}
          onRetry={() => void refetch()}
        />
      ) : null}

      <RoiTable
        rows={data?.data ?? data?.items ?? []}
        pagination={data?.pagination}
        isLoading={isPending || isRefetching}
        page={state.page}
        pageSize={state.pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
        sort={state.sort}
        onSortChange={setSort}
        selectedAsins={selectedAsins}
        onSelectRow={handleSelectRow}
        onSelectVisibleRows={handleSelectVisibleRows}
        canApprove={canApprove}
      />

      {canApprove ? (
        <RoiBulkApproveDialog
          asins={Array.from(selectedAsins)}
          isOpen={isBulkDialogOpen}
          onOpenChange={setBulkDialogOpen}
          onSuccess={handleBulkApproveSuccess}
        />
      ) : null}

    </div>
  );
}
