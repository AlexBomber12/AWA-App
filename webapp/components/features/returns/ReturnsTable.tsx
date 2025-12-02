"use client";

import Link from "next/link";
import { useMemo } from "react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable, EmptyState, PaginationControls } from "@/components/data";
import type { ReturnItem } from "@/lib/api/bffTypes";
import type { ReturnsListResponse, ReturnsSort } from "@/lib/api/returnsClient";

type SortableHeaderProps = {
  label: string;
  asc: ReturnsSort;
  desc: ReturnsSort;
  currentSort?: ReturnsSort;
  onSortChange: (sort: ReturnsSort) => void;
};

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value);

const SortableHeader = ({ label, asc, desc, currentSort, onSortChange }: SortableHeaderProps) => {
  const isAsc = currentSort === asc;
  const isDesc = currentSort === desc;
  const indicator = isAsc ? "↑" : isDesc ? "↓" : "";

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
      {indicator ? <span className="text-xs text-muted-foreground">{indicator}</span> : null}
    </button>
  );
};

type ReturnsTableProps = {
  rows: ReturnItem[];
  pagination?: ReturnsListResponse["pagination"];
  isLoading?: boolean;
  page: number;
  pageSize: number;
  sort?: ReturnsSort;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
  onSortChange: (sort: ReturnsSort) => void;
};

export function ReturnsTable({
  rows,
  pagination,
  isLoading,
  page,
  pageSize,
  sort,
  onPageChange,
  onPageSizeChange,
  onSortChange,
}: ReturnsTableProps) {
  const columns = useMemo<ColumnDef<ReturnItem>[]>(
    () => [
      {
        accessorKey: "asin",
        header: () => (
          <SortableHeader label="ASIN" asc="asin_asc" desc="asin_desc" currentSort={sort} onSortChange={onSortChange} />
        ),
        cell: ({ row }) => (
          <Link
            href={{ pathname: `/sku/${row.original.asin}`, query: { from: "returns" } }}
            className="font-semibold text-brand hover:underline"
          >
            {row.original.asin}
          </Link>
        ),
      },
      {
        accessorKey: "quantity",
        header: () => (
          <SortableHeader
            label="Units returned"
            asc="qty_asc"
            desc="qty_desc"
            currentSort={sort}
            onSortChange={onSortChange}
          />
        ),
        cell: ({ row }) => row.original.quantity.toLocaleString(),
      },
      {
        accessorKey: "reimbursementAmount",
        header: () => (
          <SortableHeader
            label="Refund amount"
            asc="refund_asc"
            desc="refund_desc"
            currentSort={sort}
            onSortChange={onSortChange}
          />
        ),
        cell: ({ row }) => <span className="font-medium">{formatCurrency(row.original.reimbursementAmount)}</span>,
      },
      {
        accessorKey: "avgRefundPerUnit",
        header: "Avg refund / unit",
        cell: ({ row }) => formatCurrency(row.original.avgRefundPerUnit ?? 0),
      },
      {
        id: "actions",
        header: "Actions",
        cell: ({ row }) => (
          <div className="flex flex-col gap-1 text-sm text-muted-foreground">
            <Link
              href={{ pathname: "/roi", query: { "filter[search]": row.original.asin } }}
              className="font-semibold text-brand hover:underline"
            >
              View in ROI
            </Link>
          </div>
        ),
      },
    ],
    [onSortChange, sort]
  );

  return (
    <div className="space-y-4">
      <DataTable
        columns={columns}
        data={rows}
        isLoading={isLoading}
        emptyState={
          <EmptyState
            title="No returns found"
            description="Adjust the date range or vendor filter to see returns in this window."
          />
        }
      />
      <PaginationControls
        page={page}
        pageSize={pageSize}
        totalItems={pagination?.total ?? rows.length}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />
    </div>
  );
}
