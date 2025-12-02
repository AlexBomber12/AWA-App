import type { Meta, StoryObj } from "@storybook/react";
import { expect, userEvent, waitFor, within } from "@storybook/test";
import type { Session } from "next-auth";

import { InboxPage } from "@/components/features/inbox/InboxPage";
import { AppShell } from "@/components/layout";
import type { InboxListResponse } from "@/lib/api/inboxClient";
import type { Task } from "@/lib/api/inboxTypes";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

const mockSession = {
  user: {
    name: "Ops Lead",
    email: "ops@example.com",
    roles: ["ops"],
  },
  expires: "",
  accessToken: "storybook-token",
} as Session & { accessToken: string };

const buildResponse = (tasks: Task[]): InboxListResponse => ({
  data: tasks,
  items: tasks,
  pagination: {
    page: 1,
    pageSize: 25,
    total: tasks.length,
    totalPages: 1,
  },
  summary: {
    open: tasks.filter((task) => task.state === "open").length,
    inProgress: tasks.filter((task) => task.state === "in_progress" || task.state === "snoozed").length,
    blocked: tasks.filter((task) => task.state === "blocked").length,
  },
});

const sampleTasks: Task[] = [
  {
    id: "task-story-101",
    type: "ROI_REVIEW",
    title: "Review ROI guardrail",
    description: "Review ROI guardrail for story SKU.",
    status: "open",
    source: "decision_engine",
    entity: { type: "sku_vendor", asin: "B00-STORY-01", vendorId: "44", label: "Storybook Yoga Mat" },
    summary: "Request discount to restore ROI guardrail",
    assignee: "Story Ops",
    state: "open",
    decision: {
      decision: "request_discount",
      priority: 95,
      deadlineAt: new Date(Date.now() + 36 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Ask vendor for 5% discount",
      why: ["ROI below 15%", { title: "Freight", detail: "Lane cost up 6%" }],
      alternatives: [
        { decision: "wait_until", label: "Observe for 24h" },
        { decision: "switch_vendor", label: "Switch to backup vendor" },
      ],
      metrics: { roi: 11.5, riskAdjustedRoi: 9.2, maxCogs: 13.4 },
    },
    priority: "critical",
    deadlineAt: new Date(Date.now() + 36 * 60 * 60 * 1000).toISOString(),
    alternatives: [
      { decision: "wait_until", label: "Observe for 24h" },
      { decision: "switch_vendor", label: "Switch to backup vendor" },
    ],
    why: ["ROI below 15%", { title: "Freight", detail: "Lane cost up 6%" }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "task-story-102",
    type: "INBOX_THREAD",
    title: "Vendor onboarding follow-up",
    description: "Complete documents for onboarding.",
    status: "in_progress",
    source: "email",
    entity: { type: "thread", threadId: "THREAD-22", label: "Vendor onboarding thread" },
    summary: "Complete vendor onboarding documents",
    assignee: "Jordan",
    state: "in_progress",
    decision: {
      decision: "continue",
      priority: "medium",
      defaultAction: "Finish onboarding checklist",
      why: ["Missing W-9", "Awaiting ACH form"],
      alternatives: [{ decision: "wait_until", label: "Hold until vendor response" }],
    },
    priority: "medium",
    why: ["Missing W-9", "Awaiting ACH form"],
    alternatives: [{ decision: "wait_until", label: "Hold until vendor response" }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

const delayedResponse = (response: Response, delayMs = 1500) =>
  new Promise<Response>((resolve) => {
    setTimeout(() => resolve(response), delayMs);
  });

type InboxStoryMode = "default" | "empty" | "error" | "loading" | "highPriority";

const buildHandlers = (mode: InboxStoryMode): FetchMockHandler[] => [
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/inbox"),
    response: () => {
      if (mode === "error") {
        return new Response(JSON.stringify({ code: "BFF_ERROR", message: "Failed to load inbox." }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (mode === "empty") {
        return new Response(JSON.stringify(buildResponse([])), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }
      const tasks: Task[] =
        mode === "highPriority"
          ? [
              {
                ...sampleTasks[0],
                id: "task-high",
                summary: "Critical ROI exception",
                decision: sampleTasks[0].decision
                  ? { ...sampleTasks[0].decision, priority: 99 }
                  : undefined,
                priority: "critical",
              },
            ]
          : sampleTasks;
      const payload = JSON.stringify(buildResponse(tasks));
      const response = new Response(payload, { status: 200, headers: { "Content-Type": "application/json" } });
      return mode === "loading" ? delayedResponse(response) : response;
    },
  },
];

const meta: Meta<typeof InboxPage> = {
  title: "Features/Inbox/InboxPage",
  component: InboxPage,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof InboxPage>;

export const Default: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("default")}>
      <AppShell initialSession={mockSession} initialPath="/inbox">
        <InboxPage />
      </AppShell>
    </FetchMock>
  ),
};

export const EmptyState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("empty")}>
      <AppShell initialSession={mockSession} initialPath="/inbox">
        <InboxPage />
      </AppShell>
    </FetchMock>
  ),
};

export const LoadingState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("loading")}>
      <AppShell initialSession={mockSession} initialPath="/inbox">
        <InboxPage />
      </AppShell>
    </FetchMock>
  ),
};

export const ErrorState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("error")}>
      <AppShell initialSession={mockSession} initialPath="/inbox">
        <InboxPage />
      </AppShell>
    </FetchMock>
  ),
};

export const HighPriority: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("highPriority")}>
      <AppShell initialSession={mockSession} initialPath="/inbox">
        <InboxPage />
      </AppShell>
    </FetchMock>
  ),
};

export const Interactive: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("default")}>
      <AppShell initialSession={mockSession} initialPath="/inbox">
        <InboxPage />
      </AppShell>
    </FetchMock>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const storyUser = userEvent.setup();

    await waitFor(() => expect(canvas.getByText("Request discount to restore ROI guardrail")).toBeInTheDocument());
    await storyUser.click(canvas.getByText("Request discount to restore ROI guardrail"));

    await waitFor(() => expect(canvas.getByText(/ROI dipped/)).toBeInTheDocument());
  },
};
