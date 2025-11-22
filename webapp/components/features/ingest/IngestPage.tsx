"use client";

import { useCallback, useEffect, useState } from "react";

import { EmptyState } from "@/components/data";
import { IngestJobForm } from "@/components/features/ingest/IngestJobForm";
import { IngestJobStatus } from "@/components/features/ingest/IngestJobStatus";
import type { IngestJobStatus as IngestJobStatusType } from "@/lib/api/ingestClient";
import { usePermissions } from "@/lib/permissions/client";

export type SessionJob = {
  taskId: string;
  status: IngestJobStatusType;
};

type IngestPageProps = {
  initialJobs?: SessionJob[] | null;
};

export function IngestPage({ initialJobs }: IngestPageProps) {
  const { can } = usePermissions();
  const canIngest = can({ resource: "ingest", action: "ingest" });
  const [jobs, setJobs] = useState<SessionJob[]>(() => initialJobs ?? []);

  useEffect(() => {
    if (initialJobs) {
      setJobs(initialJobs);
    }
  }, [initialJobs]);

  const handleJobStarted = useCallback((job: IngestJobStatusType) => {
    const taskId = typeof job?.task_id === "string" ? job.task_id : null;
    if (!taskId) {
      console.warn("Ingest job response is missing task_id", job);
      return;
    }

    setJobs((current) => {
      const filtered = current.filter((item) => item.taskId !== taskId);
      return [{ taskId, status: job }, ...filtered];
    });
  }, []);

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-border bg-background/80 p-6 shadow-sm">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold">Start an ingest job</h2>
          <p className="text-sm text-muted-foreground">
            Upload ROI/returns exports or point to S3/MinIO URIs. The ingest worker will validate, persist,
            and emit metrics for every run.
          </p>
        </div>
        <div className="mt-6">
          <IngestJobForm onJobStarted={handleJobStarted} disabled={!canIngest} />
          {!canIngest ? (
            <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
              You do not have permission to start ingest jobs. Contact an ops or admin user to run imports on your behalf.
            </p>
          ) : null}
        </div>
      </section>

      <section className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">Recent ingest jobs</h3>
          <p className="text-sm text-muted-foreground">Jobs started during this session update automatically.</p>
        </div>
        {jobs.length === 0 ? (
          <EmptyState
            title="No ingest jobs yet"
            description={
              canIngest
                ? "Submit a file or URI above to see its status tracked here."
                : "When an operator triggers ingest jobs they will appear here."
            }
          />
        ) : (
          <div className="space-y-4">
            {jobs.map((job) => (
              <IngestJobStatus key={job.taskId} taskId={job.taskId} initialStatus={job.status} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
