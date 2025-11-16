"use client";

import { type ReactNode } from "react";

import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";
import type { ApiError } from "@/lib/api/fetchFromApi";

type ErrorStateProps = {
  title?: string;
  message?: string;
  error?: ApiError | Error | string | null;
  onRetry?: () => void;
  retryLabel?: string;
  className?: string;
  actions?: ReactNode;
};

const resolveMessage = (error?: ApiError | Error | string | null, fallback?: string) => {
  if (!error) {
    return fallback ?? "Something went wrong.";
  }
  if (typeof error === "string") {
    return error;
  }
  if ("message" in error && typeof error.message === "string") {
    return error.message;
  }
  return fallback ?? "Something went wrong.";
};

export function ErrorState({
  title = "Unable to load data",
  message,
  error,
  onRetry,
  retryLabel = "Retry",
  className,
  actions,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-red-200 bg-red-50/70 px-6 py-10 text-center text-red-900 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-100",
        className
      )}
    >
      <div className="mb-3 flex size-12 items-center justify-center rounded-full border border-red-300 text-xl font-semibold">
        !
      </div>
      <p className="text-lg font-semibold">{title}</p>
      <p className="mt-1 text-sm opacity-90">{resolveMessage(error, message)}</p>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
        {onRetry ? (
          <Button variant="outline" onClick={onRetry}>
            {retryLabel}
          </Button>
        ) : null}
        {actions}
      </div>
    </div>
  );
}
