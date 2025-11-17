"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable, EmptyState, FilterBar, PaginationControls } from "@/components/data";
import { Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";

type RoiScenario = {
  id: string;
  sku: string;
  owner: string;
  status: "pending" | "approved" | "rejected";
  lastUpdated: string;
};

const ROI_COLUMNS: ColumnDef<RoiScenario>[] = [
  {
    header: "SKU",
    accessorKey: "sku",
    cell: ({ row }) => (
      <Link
        href={{ pathname: `/sku/${row.original.sku}`, query: { from: "roi" } }}
        className="font-semibold text-brand hover:underline"
      >
        {row.original.sku}
      </Link>
    ),
  },
  {
    header: "Owner",
    accessorKey: "owner",
  },
  {
    header: "Status",
    accessorKey: "status",
    cell: ({ row }) => (
      <span className="capitalize">
        {row.original.status === "pending" ? "Pending review" : row.original.status}
      </span>
    ),
  },
  {
    header: "Last updated",
    accessorKey: "lastUpdated",
  },
];

const MOCK_ROI_ROWS: RoiScenario[] = [
  { id: "1", sku: "AMZ-RED-100", owner: "Ops L1", status: "pending", lastUpdated: "2025-02-14" },
  { id: "2", sku: "AMZ-RED-425", owner: "Ops L2", status: "approved", lastUpdated: "2025-02-12" },
  { id: "3", sku: "AMZ-RED-510", owner: "Ops L1", status: "rejected", lastUpdated: "2025-02-08" },
  { id: "4", sku: "AMZ-RED-999", owner: "Ops L3", status: "pending", lastUpdated: "2025-02-06" },
];

const DEFAULT_FILTERS = {
  owner: "",
  status: "all",
};

export function RoiReviewTable() {
  const [draftFilters, setDraftFilters] = useState(DEFAULT_FILTERS);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const isDirty =
    draftFilters.owner !== filters.owner || draftFilters.status !== filters.status;

  const filteredRows = useMemo(() => {
    return MOCK_ROI_ROWS.filter((row) => {
      const matchesOwner = filters.owner
        ? row.owner.toLowerCase().includes(filters.owner.toLowerCase())
        : true;
      const matchesStatus = filters.status === "all" ? true : row.status === filters.status;
      return matchesOwner && matchesStatus;
    });
  }, [filters]);

  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);

  const handleApply = () => {
    setFilters(draftFilters);
    setPage(1);
  };

  const handleReset = () => {
    setDraftFilters(DEFAULT_FILTERS);
    setFilters(DEFAULT_FILTERS);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <FilterBar onApply={handleApply} onReset={handleReset} isDirty={isDirty}>
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold uppercase text-muted-foreground">Owner</label>
          <Input
            placeholder="Search owner"
            value={draftFilters.owner}
            onChange={(event) =>
              setDraftFilters((current) => ({ ...current, owner: event.target.value }))
            }
          />
        </div>
        <div className="flex flex-col gap-2">
          <label className="text-xs font-semibold uppercase text-muted-foreground">Status</label>
          <Select
            value={draftFilters.status}
            onValueChange={(value) =>
              setDraftFilters((current) => ({ ...current, status: value }))
            }
          >
            <SelectTrigger>
              <SelectValue placeholder="Filter status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="rejected">Rejected</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </FilterBar>

      <DataTable
        columns={ROI_COLUMNS}
        data={paginatedRows}
        emptyState={
          <EmptyState
            title="No ROI scenarios"
            description="Adjust filters or ingest new ROI runs to review them here."
          />
        }
      />

      <PaginationControls
        page={page}
        pageSize={pageSize}
        totalItems={filteredRows.length}
        onPageChange={setPage}
        onPageSizeChange={(size) => {
          setPageSize(size);
          setPage(1);
        }}
      />
    </div>
  );
}
