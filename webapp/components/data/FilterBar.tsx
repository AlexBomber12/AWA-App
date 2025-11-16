"use client";

import { type ReactNode } from "react";

import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";

type FilterBarProps = {
  children: ReactNode;
  onApply?: () => void;
  onReset?: () => void;
  isDirty?: boolean;
  disableActions?: boolean;
  className?: string;
  applyLabel?: string;
  resetLabel?: string;
};

export function FilterBar({
  children,
  onApply,
  onReset,
  isDirty = false,
  disableActions = false,
  className,
  applyLabel = "Apply filters",
  resetLabel = "Reset",
}: FilterBarProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-xl border border-border bg-background/80 p-4 shadow-sm md:flex-row md:items-end md:justify-between",
        className
      )}
    >
      <div className="flex flex-1 flex-wrap gap-4">{children}</div>
      <div className="flex items-center gap-3">
        {onReset ? (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            disabled={!isDirty || disableActions}
          >
            {resetLabel}
          </Button>
        ) : null}
        {onApply ? (
          <Button size="sm" onClick={onApply} disabled={disableActions}>
            {applyLabel}
          </Button>
        ) : null}
      </div>
    </div>
  );
}
