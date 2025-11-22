import type { Meta, StoryObj } from "@storybook/react";

import { IngestPage, type SessionJob } from "@/components/features/ingest/IngestPage";
import { AppShell, PageBody, PageHeader } from "@/components/layout";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

type IngestStoryMode = "default" | "loading" | "error";

const seededJobs: SessionJob[] = [
  {
    taskId: "TASK-STORY-SEEDED",
    status: {
      task_id: "TASK-STORY-SEEDED",
      state: "STARTED",
      meta: { progress: 0.45, target_table: "returns_raw", dialect: "returns_report" },
    },
  },
];

const delayedResponse = (response: Response, delayMs = 1200) =>
  new Promise<Response>((resolve) => setTimeout(() => resolve(response), delayMs));

const buildHandlers = (mode: IngestStoryMode): FetchMockHandler[] => [
  {
    predicate: ({ url, method }) => method === "POST" && url.includes("/api/bff/ingest"),
    response: () => {
      if (mode === "error") {
        return new Response(
          JSON.stringify({
            code: "VALIDATION_ERROR",
            message: "Please provide a valid URI or file.",
            details: { fieldErrors: { uri: "URI is required for remote ingest" } },
          }),
          { status: 422, headers: { "Content-Type": "application/json" } }
        );
      }
      return new Response(
        JSON.stringify({
          task_id: "TASK-UPLOAD-001",
          state: "PENDING",
          meta: { dialect: "returns_report", target_table: "returns_raw" },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  },
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/ingest/jobs"),
    response: ({ url }) => {
      const taskId = url.split("/").pop() ?? "TASK-UPLOAD-001";
      const payload =
        taskId === "TASK-STORY-SEEDED"
          ? {
              task_id: "TASK-STORY-SEEDED",
              state: "SUCCESS",
              meta: { rows: 1280, target_table: "returns_raw", finished_at: new Date().toISOString() },
            }
          : {
              task_id: taskId,
              state: "STARTED",
              meta: { progress: 0.2, target_table: "returns_raw", dialect: "returns_report" },
            };
      const response = new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
      return mode === "loading" ? delayedResponse(response) : response;
    },
  },
];

const meta: Meta<typeof IngestPage> = {
  title: "Features/Ingest/IngestPage",
  component: IngestPage,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof IngestPage>;

const renderIngest = (mode: IngestStoryMode, initialJobs?: SessionJob[], roles: string[] = ["ops"]) => (
  <FetchMock handlers={buildHandlers(mode)}>
    <AppShell
      initialSession={{ user: { name: "Ops Lead", email: "ops@example.com", roles }, expires: "" }}
      initialPath="/ingest"
    >
      <PageHeader
        title="Ingest"
        description="Trigger ROI/returns imports and follow their status in real time."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Ingest", active: true },
        ]}
      />
      <PageBody>
        <IngestPage initialJobs={initialJobs} />
      </PageBody>
    </AppShell>
  </FetchMock>
);

export const Default: Story = {
  render: () => renderIngest("default", seededJobs),
};

export const LoadingState: Story = {
  render: () => renderIngest("loading", seededJobs),
};

export const ErrorState: Story = {
  render: () => renderIngest("error"),
};

export const ViewerLocked: Story = {
  render: () => renderIngest("default", [], ["viewer"]),
};
