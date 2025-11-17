"use client";

import { flexRender, getCoreRowModel, type ColumnDef, useReactTable } from "@tanstack/react-table";
import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import { EmptyState } from "./EmptyState";
import { SkeletonTable } from "./SkeletonTable";

type DataTableProps<TData, TValue> = {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  isLoading?: boolean;
  className?: string;
  emptyState?: ReactNode;
  onRowClick?: (row: TData) => void;
  rowKey?: (row: TData, index: number) => string | number;
};

export function DataTable<TData, TValue>({
  columns,
  data,
  isLoading = false,
  className,
  emptyState,
  onRowClick,
  rowKey,
}: DataTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (isLoading) {
    return <SkeletonTable columns={Math.max(columns.length, 3)} />;
  }

  if (!data.length) {
    return (
      (emptyState ??
        (
          <EmptyState
            title="No data available"
            description="Once data is available it will appear in this table."
          />
        )) ?? null
    );
  }

  return (
    <div className={cn("overflow-hidden rounded-xl border border-border bg-background", className)}>
      <table className="w-full min-w-full border-collapse text-sm">
        <thead className="bg-muted/60 text-left text-xs uppercase tracking-wide text-muted-foreground">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="px-4 py-3 font-semibold">
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => {
            const key =
              rowKey?.(row.original, row.index) ??
              (typeof row.original === "object" && row.original !== null && "id" in row.original
                ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  ((row.original as any).id as string | number)
                : row.id);
            const clickable = Boolean(onRowClick);
            return (
              <tr
                key={key}
                className={cn(
                  "border-t border-border text-sm transition-colors",
                  clickable ? "cursor-pointer hover:bg-muted/50" : undefined
                )}
                onClick={clickable ? () => onRowClick?.(row.original) : undefined}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
