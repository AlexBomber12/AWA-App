"use client";

import { Button, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";

type PaginationControlsProps = {
  page: number;
  pageSize: number;
  totalItems: number;
  onPageChange?: (page: number) => void;
  onPageSizeChange?: (pageSize: number) => void;
  pageSizeOptions?: number[];
};

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 25, 50];

export function PaginationControls({
  page,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
}: PaginationControlsProps) {
  const totalPages = Math.max(1, Math.ceil(Math.max(totalItems, 0) / pageSize));

  const canGoBack = page > 1;
  const canGoForward = page < totalPages;

  const handlePrev = () => {
    if (canGoBack && onPageChange) {
      onPageChange(page - 1);
    }
  };

  const handleNext = () => {
    if (canGoForward && onPageChange) {
      onPageChange(page + 1);
    }
  };

  return (
    <div className="flex flex-col items-start gap-3 text-sm text-muted-foreground md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-3">
        <span>Rows per page</span>
        <Select
          value={String(pageSize)}
          onValueChange={(value) => onPageSizeChange?.(Number(value))}
        >
          <SelectTrigger className="w-20">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {pageSizeOptions.map((size) => (
              <SelectItem key={size} value={String(size)}>
                {size}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="flex items-center gap-4">
        <span>
          Page {page} of {totalPages}
        </span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handlePrev} disabled={!canGoBack}>
            Previous
          </Button>
          <Button variant="outline" size="sm" onClick={handleNext} disabled={!canGoForward}>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
}
