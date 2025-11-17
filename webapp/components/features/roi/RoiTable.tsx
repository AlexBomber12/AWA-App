"use client";

import { useCallback, useMemo } from "react";
import type { ColumnDef, Row } from "@tanstack/react-table";
import { useRouter } from "next/navigation";

import { PaginationControls, VirtualizedTable } from "@/components/data";
import { Checkbox } from "@/components/ui";

import type { RoiListResponse, RoiRow } from "./types";
import type { RoiSort } from "./tableState";

type RoiTableProps = {
  rows: RoiRow[];
  pagination?: RoiListResponse["pagination"];
  isLoading?: boolean;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  sort?: RoiSort;
  onSortChange: (sort: RoiSort) => void;
  selectedAsins: Set<string>;
  onSelectRow: (asin: string, checked: boolean) => void;
  onSelectVisibleRows: (asins: string[], checked: boolean) => void;
  canApprove: boolean;
};

type SortableHeaderProps = {
  label: string;
  asc: RoiSort;
  desc: RoiSort;
  currentSort?: RoiSort;
  onSortChange: (sort: RoiSort) => void;
};

const formatCurrency = (value?: number | null) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "–";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercent = (value?: number | null) => {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "–";
  }
  return `${value.toFixed(1)}%`;
};

const getMarginValue = (row: RoiRow): number => {
  const roiPct = row.roi_pct ?? 0;
  const totalCost = (row.cost ?? 0) + (row.freight ?? 0) + (row.fees ?? 0);
  return (roiPct / 100) * totalCost;
};

const SortableHeader = ({ label, asc, desc, currentSort, onSortChange }: SortableHeaderProps) => {
  const isAsc = currentSort === asc;
  const isDesc = currentSort === desc;
  const direction = isAsc ? "↑" : isDesc ? "↓" : "";

  const handleClick = () => {
    if (isAsc) {
      onSortChange(desc);
      return;
    }
    if (isDesc) {
      onSortChange(asc);
      return;
    }
    onSortChange(desc);
  };

  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 text-left font-semibold"
      onClick={handleClick}
    >
      <span>{label}</span>
      {direction ? <span className="text-xs text-muted-foreground">{direction}</span> : null}
    </button>
  );
};

export function RoiTable({
  rows,
  pagination,
  isLoading,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  sort,
  onSortChange,
  selectedAsins,
  onSelectRow,
  onSelectVisibleRows,
  canApprove,
}: RoiTableProps) {
  const router = useRouter();

  const visibleAsins = useMemo(
    () => rows.map((row) => row.asin).filter(Boolean),
    [rows]
  );
  const selectedVisible = visibleAsins.filter((asin) => selectedAsins.has(asin));
  const allVisibleSelected = visibleAsins.length > 0 && selectedVisible.length === visibleAsins.length;
  const partiallySelected =
    selectedVisible.length > 0 && selectedVisible.length < visibleAsins.length;

  const goToSku = useCallback((asin: string) => {
    void router.push(`/sku/${asin}`);
  }, [router]);

  const columns = useMemo<ColumnDef<RoiRow>[]>(
    () => {
      const tableColumns: ColumnDef<RoiRow>[] = [];

      if (canApprove) {
        tableColumns.push({
          id: "selection",
          header: () => (
            <Checkbox
              aria-label="Select visible rows"
              checked={allVisibleSelected}
              indeterminate={partiallySelected}
              onChange={(event) => onSelectVisibleRows(visibleAsins, event.target.checked)}
            />
          ),
          cell: ({ row }) => (
            <Checkbox
              aria-label={`Select ${row.original.asin}`}
              checked={selectedAsins.has(row.original.asin ?? "")}
              onChange={(event) => onSelectRow(row.original.asin ?? "", event.target.checked)}
            />
          ),
          size: 48,
        });
      }

      tableColumns.push(
        {
          accessorKey: "asin",
          header: () => (
            <SortableHeader
              label="SKU"
              asc="asin_asc"
              desc="asin_desc"
              currentSort={sort}
              onSortChange={onSortChange}
            />
          ),
          cell: ({ row }) => (
            <button
              type="button"
              className="font-semibold text-brand hover:underline"
              onClick={() => goToSku(row.original.asin)}
            >
              {row.original.asin}
            </button>
          ),
        },
        {
          accessorKey: "title",
          header: "Title",
          cell: ({ row }) => (
            <div className="max-w-xs truncate text-sm text-muted-foreground">{row.original.title ?? "—"}</div>
          ),
        },
        {
          accessorKey: "vendor_id",
          header: () => (
            <SortableHeader
              label="Vendor"
              asc="vendor_asc"
              desc="vendor_desc"
              currentSort={sort}
              onSortChange={onSortChange}
            />
          ),
          cell: ({ row }) => <span>{row.original.vendor_id ?? "—"}</span>,
        },
        {
          accessorKey: "category",
          header: "Category",
          cell: ({ row }) => <span>{row.original.category ?? "—"}</span>,
        },
        {
          accessorKey: "cost",
          header: "Cost",
          cell: ({ row }) => <span>{formatCurrency(row.original.cost)}</span>,
        },
        {
          accessorKey: "freight",
          header: "Freight",
          cell: ({ row }) => <span>{formatCurrency(row.original.freight)}</span>,
        },
        {
          accessorKey: "fees",
          header: "Fees",
          cell: ({ row }) => <span>{formatCurrency(row.original.fees)}</span>,
        },
        {
          id: "margin",
          header: () => (
            <SortableHeader
              label="Margin"
              asc="margin_asc"
              desc="margin_desc"
              currentSort={sort}
              onSortChange={onSortChange}
            />
          ),
          cell: ({ row }) => <span>{formatCurrency(getMarginValue(row.original))}</span>,
        },
        {
          accessorKey: "roi_pct",
          header: () => (
            <SortableHeader
              label="ROI %"
              asc="roi_pct_asc"
              desc="roi_pct_desc"
              currentSort={sort}
              onSortChange={onSortChange}
            />
          ),
          cell: ({ row }) => (
            <span className="font-semibold">{formatPercent(row.original.roi_pct)}</span>
          ),
        }
      );

      return tableColumns;
    },
    [
      allVisibleSelected,
      canApprove,
      goToSku,
      onSelectRow,
      onSelectVisibleRows,
      selectedAsins,
      sort,
      onSortChange,
      partiallySelected,
      visibleAsins,
    ]
  );

  return (
    <div className="space-y-4">
      <VirtualizedTable
        columns={columns}
        data={rows}
        getRowId={(original, index) => original.asin ?? `row-${index}`}
        height={520}
        isLoading={isLoading}
        getRowClassName={(row: Row<RoiRow>) =>
          selectedAsins.has(row.original.asin ?? "") ? "bg-brand/5" : undefined
        }
      />
      <PaginationControls
        page={page}
        pageSize={pageSize}
        totalItems={pagination?.total ?? 0}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    </div>
  );
}
