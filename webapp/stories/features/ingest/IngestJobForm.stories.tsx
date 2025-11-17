import type { Meta, StoryObj } from "@storybook/react";
import { useMemo } from "react";

import { IngestJobForm } from "@/components/features/ingest/IngestJobForm";
import type { IngestJobStatus } from "@/lib/api/ingestClient";

import { FetchMock, type FetchMockHandler } from "./fetchMock";

const mockJob: IngestJobStatus = {
  task_id: "TASK-STORY-INGEST",
  state: "PENDING",
  meta: {
    dialect: "returns_report",
    target_table: "returns_raw",
  },
};

const successHandlers: FetchMockHandler[] = [
  {
    predicate: (info) => info.method === "POST" && info.url.includes("/api/bff/ingest"),
    response: () =>
      new Response(JSON.stringify(mockJob), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
  },
];

const validationHandlers: FetchMockHandler[] = [
  {
    predicate: (info) => info.method === "POST" && info.url.includes("/api/bff/ingest"),
    response: () =>
      new Response(
        JSON.stringify({
          code: "VALIDATION_ERROR",
          message: "Please fix the highlighted fields.",
          status: 422,
          details: {
            fieldErrors: {
              file: "Unsupported file format",
            },
          },
        }),
        {
          status: 422,
          headers: { "Content-Type": "application/json" },
        }
      ),
  },
];

const meta: Meta<typeof IngestJobForm> = {
  title: "Features/Ingest/IngestJobForm",
  component: IngestJobForm,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof IngestJobForm>;

export const Default: Story = {
  render: () => {
    const handlers = useMemo(() => successHandlers, []);
    return (
      <FetchMock handlers={handlers}>
        <div className="mx-auto max-w-2xl space-y-4 p-6">
          <IngestJobForm onJobStarted={(job) => console.log("job started", job)} />
        </div>
      </FetchMock>
    );
  },
};

export const ServerValidationError: Story = {
  render: () => {
    const handlers = useMemo(() => validationHandlers, []);
    return (
      <FetchMock handlers={handlers}>
        <div className="mx-auto max-w-2xl space-y-4 p-6">
          <IngestJobForm />
        </div>
      </FetchMock>
    );
  },
};
