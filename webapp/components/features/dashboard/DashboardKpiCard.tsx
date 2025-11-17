"use client";

import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

type Severity = "neutral" | "positive" | "warning";

const severityStyles: Record<Severity, string> = {
  neutral: "border-border",
  positive: "border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-900/10 dark:text-emerald-200",
  warning: "border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200",
};

type DashboardKpiCardProps = {
  title: string;
  value: string;
  helperText?: string;
  deltaLabel?: string;
  tooltip?: string;
  severity?: Severity;
};

export function DashboardKpiCard({
  title,
  value,
  helperText,
  deltaLabel,
  tooltip,
  severity = "neutral",
}: DashboardKpiCardProps) {
  return (
    <div className="rounded-2xl border border-border bg-background/80 p-6 shadow-sm">
      <div className="flex items-start gap-2">
        <div className="flex flex-1 items-center gap-2">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {tooltip ? (
            <TooltipProvider delayDuration={150}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    type="button"
                    aria-label={`Learn more about ${title}`}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <InfoIcon />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top">{tooltip}</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          ) : null}
        </div>
        {deltaLabel ? (
          <span
            className={cn(
              "rounded-full border px-2 py-0.5 text-xs font-semibold uppercase",
              severityStyles[severity]
            )}
          >
            {deltaLabel}
          </span>
        ) : null}
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p>
      {helperText ? <p className="mt-1 text-sm text-muted-foreground">{helperText}</p> : null}
    </div>
  );
}
const InfoIcon = () => (
  <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
    <circle cx="12" cy="12" r="10" fill="currentColor" opacity="0.14" />
    <path
      d="M12 7.25a.75.75 0 1 1 0 1.5.75.75 0 0 1 0-1.5Zm-.88 3.13a.88.88 0 0 1 1.76 0v6.24a.88.88 0 0 1-1.76 0Z"
      fill="currentColor"
    />
  </svg>
);
