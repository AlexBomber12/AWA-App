"use client";

type SkeletonTableProps = {
  columns?: number;
  rows?: number;
};

export function SkeletonTable({ columns = 4, rows = 5 }: SkeletonTableProps) {
  return (
    <div className="w-full rounded-xl border border-border bg-background/60 p-4">
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={`skeleton-row-${rowIndex}`} className="grid gap-3" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
            {Array.from({ length: columns }).map((__, colIndex) => (
              <div key={`skeleton-cell-${rowIndex}-${colIndex}`} className="h-5 animate-pulse rounded bg-muted/60" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
