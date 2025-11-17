"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable, EmptyState, PaginationControls } from "@/components/data";

type ReturnRow = {
  id: string;
  asin: string;
  sku: string;
  reason: string;
  status: "open" | "investigating" | "closed";
  units: number;
  submittedAt: string;
};

const RETURNS_COLUMNS: ColumnDef<ReturnRow>[] = [
  {
    header: "ASIN",
    accessorKey: "asin",
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
    header: "SKU",
    accessorKey: "sku",
  },
  {
    header: "Reason",
    accessorKey: "reason",
  },
  {
    header: "Status",
    accessorKey: "status",
    cell: ({ row }) => (
      <span className="capitalize text-muted-foreground">{row.original.status}</span>
    ),
  },
  {
    header: "Units",
    accessorKey: "units",
    cell: ({ row }) => row.original.units.toLocaleString(),
  },
  {
    header: "Submitted",
    accessorKey: "submittedAt",
  },
];

const MOCK_RETURNS: ReturnRow[] = [
  {
    id: "r1",
    asin: "B00-MSKU-01",
    sku: "AMZ-BLUE-100",
    reason: "Damaged packaging",
    status: "open",
    units: 18,
    submittedAt: "2025-02-13",
  },
  {
    id: "r2",
    asin: "B00-MSKU-02",
    sku: "AMZ-BLUE-200",
    reason: "Defective unit",
    status: "investigating",
    units: 6,
    submittedAt: "2025-02-12",
  },
  {
    id: "r3",
    asin: "B00-MSKU-03",
    sku: "AMZ-BLUE-350",
    reason: "Late delivery",
    status: "closed",
    units: 11,
    submittedAt: "2025-02-10",
  },
  {
    id: "r4",
    asin: "B00-MSKU-04",
    sku: "AMZ-BLUE-410",
    reason: "Wrong color shipped",
    status: "open",
    units: 4,
    submittedAt: "2025-02-08",
  },
  {
    id: "r5",
    asin: "B00-MSKU-05",
    sku: "AMZ-BLUE-525",
    reason: "Accessory missing",
    status: "investigating",
    units: 9,
    submittedAt: "2025-02-06",
  },
];

const PAGE_SIZE = 5;

export function ReturnsQueueTable() {
  const [page, setPage] = useState(1);

  const paginatedRows = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return MOCK_RETURNS.slice(start, start + PAGE_SIZE);
  }, [page]);

  return (
    <div className="space-y-4">
      <DataTable
        columns={RETURNS_COLUMNS}
        data={paginatedRows}
        emptyState={
          <EmptyState
            title="No return batches"
            description="Ingest will populate returns queues as soon as SP-API emits return posts."
          />
        }
      />
      <PaginationControls
        page={page}
        pageSize={PAGE_SIZE}
        totalItems={MOCK_RETURNS.length}
        onPageChange={setPage}
        onPageSizeChange={() => {
          /* PAGE_SIZE is fixed for the mocked view */
        }}
      />
    </div>
  );
}
