import type { Meta, StoryObj } from "@storybook/react";
import { useMemo } from "react";

import { IngestJobStatus } from "@/components/features/ingest/IngestJobStatus";
import type { IngestJobStatus as IngestJobStatusType } from "@/lib/api/ingestClient";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

const pendingJob: IngestJobStatusType = {
  task_id: "TASK-PENDING",
  state: "PENDING",
  meta: {},
};

const runningJob: IngestJobStatusType = {
  task_id: "TASK-RUNNING",
  state: "STARTED",
  meta: {
    progress: 0.42,
    dialect: "returns_report",
    target_table: "returns_raw",
    started_at: new Date().toISOString(),
  },
};

const successJob: IngestJobStatusType = {
  task_id: "TASK-SUCCESS",
  state: "SUCCESS",
  meta: {
    rows: 452,
    dialect: "returns_report",
    target_table: "returns_raw",
    finished_at: new Date().toISOString(),
  },
};

const failureJob: IngestJobStatusType = {
  task_id: "TASK-FAILURE",
  state: "FAILURE",
  meta: {
    error: "Validation failed: missing column(s)",
    status: "error",
    finished_at: new Date().toISOString(),
  },
};

const meta: Meta<typeof IngestJobStatus> = {
  title: "Features/Ingest/IngestJobStatus",
  component: IngestJobStatus,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof IngestJobStatus>;

export const Pending: Story = {
  args: {
    taskId: "TASK-PENDING",
    initialStatus: pendingJob,
    pollingDisabled: true,
  },
  render: (args) => (
    <div className="mx-auto max-w-3xl p-6">
      <IngestJobStatus {...args} />
    </div>
  ),
};

export const Running: Story = {
  args: {
    taskId: "TASK-RUNNING",
    initialStatus: runningJob,
    pollingDisabled: true,
  },
  render: (args) => (
    <div className="mx-auto max-w-3xl p-6">
      <IngestJobStatus {...args} />
    </div>
  ),
};

export const Success: Story = {
  args: {
    taskId: "TASK-SUCCESS",
    initialStatus: successJob,
    pollingDisabled: true,
  },
  render: (args) => (
    <div className="mx-auto max-w-3xl p-6">
      <IngestJobStatus {...args} />
    </div>
  ),
};

export const Failure: Story = {
  args: {
    taskId: "TASK-FAILURE",
    initialStatus: failureJob,
    pollingDisabled: true,
  },
  render: (args) => (
    <div className="mx-auto max-w-3xl p-6">
      <IngestJobStatus {...args} />
    </div>
  ),
};

export const TransitionToSuccess: Story = {
  render: () => {
    const handlers = useMemo<FetchMockHandler[]>(() => {
      let calls = 0;
      return [
        {
          predicate: (info) => info.method === "GET" && info.url.includes("/api/bff/ingest/jobs/TASK-POLL"),
          response: () => {
            calls += 1;
            const payload = calls >= 3 ? successJob : runningJob;
            return new Response(JSON.stringify({ ...payload, task_id: "TASK-POLL" }), {
              status: 200,
              headers: { "Content-Type": "application/json" },
            });
          },
        },
      ];
    }, []);

    return (
      <FetchMock handlers={handlers}>
        <div className="mx-auto max-w-3xl p-6">
          <IngestJobStatus
            taskId="TASK-POLL"
            initialStatus={{ ...pendingJob, task_id: "TASK-POLL" }}
            pollingIntervalMs={2000}
          />
        </div>
      </FetchMock>
    );
  },
};

export const PollingErrors: Story = {
  render: () => {
    const handlers = useMemo<FetchMockHandler[]>(() => {
      return [
        {
          predicate: ({ url }) => url.includes("/api/bff/ingest/jobs/TASK-ERR"),
          response: () =>
            new Response(
              JSON.stringify({
                code: "RETRYABLE",
                message: "Temporary ingest service outage",
              }),
              { status: 503, headers: { "Content-Type": "application/json" } }
            ),
        },
      ];
    }, []);

    return (
      <FetchMock handlers={handlers}>
        <div className="mx-auto max-w-3xl p-6">
          <IngestJobStatus taskId="TASK-ERR" pollingIntervalMs={1000} />
        </div>
      </FetchMock>
    );
  },
};
