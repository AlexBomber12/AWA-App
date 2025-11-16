import type { Meta, StoryObj } from "@storybook/react";
import { useMemo, useState } from "react";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable, EmptyState, FilterBar, PaginationControls } from "@/components/data";
import { Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";

type DemoRow = {
  id: string;
  sku: string;
  owner: string;
  status: "pending" | "approved";
};

const columns: ColumnDef<DemoRow>[] = [
  { header: "SKU", accessorKey: "sku" },
  { header: "Owner", accessorKey: "owner" },
  {
    header: "Status",
    accessorKey: "status",
    cell: ({ row }) => <span className="capitalize">{row.original.status}</span>,
  },
];

const rows: DemoRow[] = [
  { id: "1", sku: "SKU-100", owner: "Ops L1", status: "pending" },
  { id: "2", sku: "SKU-101", owner: "Ops L2", status: "approved" },
  { id: "3", sku: "SKU-102", owner: "Ops L1", status: "pending" },
  { id: "4", sku: "SKU-103", owner: "Ops L3", status: "approved" },
];

const meta: Meta = {
  title: "Data/DataTable",
};

export default meta;

export const WithFilters: StoryObj = {
  render: () => {
    const [status, setStatus] = useState("all");
    const [owner, setOwner] = useState("");
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(2);

    const filtered = useMemo(() => {
      return rows.filter((row) => {
        const hasOwner = owner ? row.owner.toLowerCase().includes(owner.toLowerCase()) : true;
        const hasStatus = status === "all" ? true : row.status === status;
        return hasOwner && hasStatus;
      });
    }, [owner, status]);

    const paged = filtered.slice((page - 1) * pageSize, page * pageSize);

    return (
      <div className="space-y-6 p-6">
        <FilterBar onApply={() => setPage(1)} onReset={() => { setOwner(""); setStatus("all"); setPage(1); }} isDirty={Boolean(owner) || status !== "all"}>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase text-muted-foreground">Owner</label>
            <Input value={owner} onChange={(event) => setOwner(event.target.value)} placeholder="Search owner" />
          </div>
          <div className="flex flex-col gap-2">
            <label className="text-xs font-semibold uppercase text-muted-foreground">Status</label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="approved">Approved</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </FilterBar>
        <DataTable
          columns={columns}
          data={paged}
          emptyState={
            <EmptyState
              title="No rows"
              description="Adjust filters to see how the table responds."
            />
          }
        />
        <PaginationControls
          page={page}
          pageSize={pageSize}
          totalItems={filtered.length}
          onPageChange={setPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setPage(1);
          }}
        />
      </div>
    );
  },
};
