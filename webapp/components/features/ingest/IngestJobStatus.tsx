"use client";

// Pattern: long-running job status + polling

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui";
import type { ApiError } from "@/lib/api/apiError";
import { getIngestJobStatus, type IngestJobStatus } from "@/lib/api/ingestClient";
import { usePollingQuery } from "@/lib/api/usePollingQuery";
import { cn } from "@/lib/utils";

type IngestJobStatusProps = {
  taskId: string;
  initialStatus?: IngestJobStatus;
  className?: string;
  compact?: boolean;
  pollingIntervalMs?: number;
  maxDurationMs?: number;
  pollingDisabled?: boolean;
};

const TERMINAL_STATES = new Set(["SUCCESS", "FAILURE", "REVOKED"]);
const RUNNING_STATES = new Set(["PENDING", "RECEIVED", "STARTED", "RETRY"]);

const jobStatusQueryKey = (taskId: string) => ["ingest", "job-status", taskId] as const;

const isTerminalState = (state: unknown): boolean => {
  if (typeof state !== "string") {
    return false;
  }
  return TERMINAL_STATES.has(state.toUpperCase());
};

const resolveVisualState = (state: unknown) => {
  const normalized = typeof state === "string" ? state.toUpperCase() : "PENDING";
  if (normalized === "SUCCESS") {
    return {
      label: "Completed",
      description: "The ingest job finished successfully.",
      tone: "success" as const,
    };
  }
  if (normalized === "FAILURE") {
    return {
      label: "Failed",
      description: "The ingest job failed. Review the error for guidance.",
      tone: "danger" as const,
    };
  }
  if (normalized === "REVOKED") {
    return {
      label: "Canceled",
      description: "The job was canceled before completion.",
      tone: "danger" as const,
    };
  }
  if (RUNNING_STATES.has(normalized)) {
    return {
      label: "Running",
      description: "The ingest worker is processing this job.",
      tone: "info" as const,
    };
  }
  return {
    label: "Pending",
    description: "The job is queued and waiting for the ingest worker.",
    tone: "muted" as const,
  };
};

const toneStyles: Record<ReturnType<typeof resolveVisualState>["tone"], { pill: string; dot: string }> = {
  success: {
    pill: "bg-emerald-50 text-emerald-800 border border-emerald-200",
    dot: "bg-emerald-500",
  },
  danger: {
    pill: "bg-red-50 text-red-800 border border-red-200",
    dot: "bg-red-500",
  },
  info: {
    pill: "bg-sky-50 text-sky-800 border border-sky-200",
    dot: "bg-sky-500",
  },
  muted: {
    pill: "bg-amber-50 text-amber-800 border border-amber-200",
    dot: "bg-amber-500",
  },
};

const formatTimestamp = (value: unknown): string | null => {
  if (typeof value !== "string" || !value) {
    return null;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return null;
  }
  return date.toLocaleString();
};

const Spinner = () => (
  <span
    className="inline-flex size-3 animate-spin rounded-full border border-current border-t-transparent"
    aria-hidden="true"
  />
);

export function IngestJobStatus({
  taskId,
  initialStatus,
  className,
  compact = false,
  pollingIntervalMs,
  maxDurationMs,
  pollingDisabled = false,
}: IngestJobStatusProps) {
  const [lastError, setLastError] = useState<ApiError | null>(null);
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [pollingPaused, setPollingPaused] = useState(false);

  const query = usePollingQuery<IngestJobStatus, ApiError, IngestJobStatus, ReturnType<typeof jobStatusQueryKey>>({
    queryKey: jobStatusQueryKey(taskId),
    queryFn: () => getIngestJobStatus(taskId),
    enabled: Boolean(taskId) && !pollingDisabled && !pollingPaused,
    initialData: initialStatus,
    stopWhen: (status) => isTerminalState(status?.state),
    pollingIntervalMs,
    maxDurationMs,
    retry: 0,
    onError: (error) => {
      setLastError(error);
      setConsecutiveErrors((current) => {
        const next = current + 1;
        if (next >= 3) {
          setPollingPaused(true);
        }
        return next;
      });
    },
  });

  useEffect(() => {
    if (query.data) {
      setLastError(null);
      setConsecutiveErrors(0);
    }
  }, [query.data]);

  const job = query.data ?? initialStatus;
  const isLoading = query.isPending && !job;

  const visual = resolveVisualState(job?.state);
  const tone = toneStyles[visual.tone];
  const meta = (job?.meta ?? {}) as Record<string, unknown>;
  const rows = typeof meta.rows === "number" ? meta.rows : null;
  const dialect = typeof meta.dialect === "string" ? meta.dialect : null;
  const targetTable = typeof meta.target_table === "string" ? meta.target_table : null;
  const errorMessage = typeof meta.error === "string" ? meta.error : null;
  const statusNote = typeof meta.status === "string" ? meta.status : null;
  const progressValue = typeof meta.progress === "number" ? meta.progress : null;
  const progressPct = useMemo(() => {
    if (typeof progressValue !== "number") {
      return null;
    }
    if (progressValue <= 1) {
      return Math.round(progressValue * 100);
    }
    if (progressValue <= 100) {
      return Math.round(progressValue);
    }
    return 100;
  }, [progressValue]);

  const finishedAt = formatTimestamp(meta.finished_at);
  const startedAt = formatTimestamp(meta.started_at);

  const lastUpdatedText = query.dataUpdatedAt
    ? new Date(query.dataUpdatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : "Not yet fetched";

  const containerClass = cn(
    "rounded-xl border border-border bg-background/80 shadow-sm",
    compact ? "p-4" : "p-6",
    className
  );

  const handleResumePolling = () => {
    setPollingPaused(false);
    setConsecutiveErrors(0);
    setLastError(null);
    void query.refetch();
  };

  const showErrorBanner = lastError !== null;

  return (
    <div className={containerClass}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Task ID</p>
          <p className="font-mono text-sm text-foreground">{taskId}</p>
        </div>
        <div className={cn("inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold", tone.pill)}>
          <span className={cn("size-2 rounded-full", tone.dot)} />
          {visual.label}
        </div>
      </div>

      {isLoading ? (
        <div className="mt-5 h-16 animate-pulse rounded-lg bg-muted/40" />
      ) : (
        <div className={cn("mt-4", compact ? "text-sm" : "text-base")}
        >
          <p className="font-medium text-foreground">{visual.description}</p>
          <dl className="mt-4 grid gap-3 text-sm text-muted-foreground sm:grid-cols-2">
            {rows !== null ? (
              <div>
                <dt className="font-medium text-foreground">Rows processed</dt>
                <dd>{rows.toLocaleString()}</dd>
              </div>
            ) : null}
            {dialect ? (
              <div>
                <dt className="font-medium text-foreground">Dialect</dt>
                <dd className="font-mono text-xs text-foreground/80">{dialect}</dd>
              </div>
            ) : null}
            {targetTable ? (
              <div>
                <dt className="font-medium text-foreground">Target table</dt>
                <dd className="font-mono text-xs text-foreground/80">{targetTable}</dd>
              </div>
            ) : null}
            {progressPct !== null ? (
              <div>
                <dt className="font-medium text-foreground">Progress</dt>
                <dd>{progressPct}%</dd>
              </div>
            ) : null}
            {startedAt ? (
              <div>
                <dt className="font-medium text-foreground">Started</dt>
                <dd>{startedAt}</dd>
              </div>
            ) : null}
            {finishedAt ? (
              <div>
                <dt className="font-medium text-foreground">Finished</dt>
                <dd>{finishedAt}</dd>
              </div>
            ) : null}
          </dl>
          {statusNote && !errorMessage ? (
            <p className="mt-3 text-sm text-muted-foreground">Status: {statusNote}</p>
          ) : null}
          {errorMessage ? (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900">
              {errorMessage}
            </div>
          ) : null}
        </div>
      )}

      {showErrorBanner ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <p className="font-semibold">Unable to refresh job status</p>
          <p className="mt-1 text-xs opacity-80">{lastError?.message ?? "Unexpected BFF error."}</p>
          {pollingPaused ? (
            <p className="mt-1 text-xs opacity-70">
              Polling paused after {consecutiveErrors} consecutive failures. Resume when ready.
            </p>
          ) : null}
          <div className="mt-3 flex flex-wrap gap-2">
            <Button size="sm" variant="outline" onClick={() => void query.refetch()}>
              Retry now
            </Button>
            {pollingPaused ? (
              <Button size="sm" variant="ghost" onClick={handleResumePolling}>
                Resume polling
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
        <span>Last updated {lastUpdatedText}</span>
        <div className="flex items-center gap-2">
          {query.isFetching ? (
            <span className="inline-flex items-center gap-1">
              <Spinner />
              Refreshing…
            </span>
          ) : null}
          <Button size="sm" variant="outline" onClick={() => void query.refetch()} disabled={query.isFetching}>
            Refresh
          </Button>
        </div>
      </div>
    </div>
  );
}
