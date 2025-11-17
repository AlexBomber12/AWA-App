"use client";

import {
  flexRender,
  getCoreRowModel,
  type ColumnDef,
  type Row,
  type Table as TanstackTable,
  useReactTable,
} from "@tanstack/react-table";
import { useMemo, useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { type ReactNode } from "react";

import { cn } from "@/lib/utils";

import { EmptyState } from "./EmptyState";
import { SkeletonTable } from "./SkeletonTable";

type VirtualizedTableProps<TData, TValue> = {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  getRowId?: (originalRow: TData, index: number) => string;
  height?: number;
  estimatedRowHeight?: number;
  overscan?: number;
  className?: string;
  isLoading?: boolean;
  emptyState?: ReactNode;
  onRowClick?: (row: TData) => void;
  getRowClassName?: (row: Row<TData>, index: number) => string | undefined;
};

const DEFAULT_HEIGHT = 520;
const DEFAULT_ROW_HEIGHT = 52;
const DEFAULT_OVERSCAN = 8;

const renderEmptyState = (emptyState?: ReactNode) =>
  emptyState ?? (
    <EmptyState
      title="No rows"
      description="Adjust filters to update the current table results."
    />
  );

const renderHeader = <TData, TValue>(table: TanstackTable<TData>, columnCount: number) => {
  const headerGroups = table.getHeaderGroups();
  return (
    <thead className="sticky top-0 z-10 bg-muted/70 text-left text-xs uppercase tracking-wide text-muted-foreground">
      {headerGroups.map((headerGroup) => (
        <tr key={headerGroup.id}>
          {headerGroup.headers.map((header) => (
            <th key={header.id} colSpan={header.colSpan} className="px-4 py-3 font-semibold">
              {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
            </th>
          ))}
        </tr>
      ))}
      {columnCount === 0 ? (
        <tr>
          <th className="px-4 py-3 font-semibold">No columns</th>
        </tr>
      ) : null}
    </thead>
  );
};

export function VirtualizedTable<TData, TValue>({
  columns,
  data,
  getRowId,
  height = DEFAULT_HEIGHT,
  estimatedRowHeight = DEFAULT_ROW_HEIGHT,
  overscan = DEFAULT_OVERSCAN,
  className,
  isLoading,
  emptyState,
  onRowClick,
  getRowClassName,
}: VirtualizedTableProps<TData, TValue>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getRowId,
  });

  const rows = table.getRowModel().rows;
  const columnCount = table.getVisibleLeafColumns().length;

  const parentRef = useRef<HTMLDivElement>(null);

  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimatedRowHeight,
    overscan,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();
  const paddingTop = virtualRows.length > 0 ? virtualRows[0]!.start : 0;
  const paddingBottom =
    virtualRows.length > 0
      ? rowVirtualizer.getTotalSize() - virtualRows[virtualRows.length - 1]!.end
      : 0;

  const handleRowClick = useMemo(() => {
    if (!onRowClick) {
      return null;
    }
    return (row: Row<TData>) => onRowClick(row.original);
  }, [onRowClick]);

  if (isLoading) {
    return <SkeletonTable columns={Math.max(columnCount, 3)} />;
  }

  if (!rows.length) {
    return renderEmptyState(emptyState);
  }

  return (
    <div className={cn("overflow-hidden rounded-xl border border-border bg-background", className)}>
      <div
        ref={parentRef}
        className="max-h-full overflow-auto"
        style={{ height }}
      >
        <table className="w-full min-w-full border-collapse text-sm">
          {renderHeader(table, columnCount)}
          <tbody>
            {paddingTop > 0 ? (
              <tr>
                <td style={{ height: `${paddingTop}px` }} colSpan={columnCount} />
              </tr>
            ) : null}
            {virtualRows.map((virtualRow) => {
              const row = rows[virtualRow.index]!;
              const clickable = Boolean(handleRowClick);
              const extraClassName = getRowClassName?.(row, virtualRow.index);
              return (
                <tr
                  key={row.id}
                  className={cn(
                    "border-t border-border transition-colors",
                    clickable ? "cursor-pointer hover:bg-muted/50" : undefined,
                    extraClassName
                  )}
                  style={{ height: `${virtualRow.size}px` }}
                  onClick={clickable ? () => handleRowClick?.(row) : undefined}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 align-middle">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
            {paddingBottom > 0 ? (
              <tr>
                <td style={{ height: `${paddingBottom}px` }} colSpan={columnCount} />
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
