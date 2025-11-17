import type { Meta, StoryObj } from "@storybook/react";
import type { Session } from "next-auth";

import { ReturnsPage } from "@/components/features/returns/ReturnsPage";
import { AppShell } from "@/components/layout";
import type { ReturnsListResponse, ReturnsSummary } from "@/lib/api/returnsClient";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

const mockSession = {
  user: {
    name: "Ops Lead",
    email: "ops@example.com",
    roles: ["admin"],
  },
  expires: "",
  accessToken: "storybook-token",
} as Session & { accessToken: string };

const listResponse: ReturnsListResponse = {
  items: [
    { asin: "B00-RET-001", qty: 42, refundAmount: 1299.5, avgRefundPerUnit: 30.94 },
    { asin: "B00-RET-002", qty: 18, refundAmount: 420.0, avgRefundPerUnit: 23.33 },
    { asin: "B00-RET-003", qty: 64, refundAmount: 1999.99, avgRefundPerUnit: 31.25 },
  ],
  pagination: {
    page: 1,
    pageSize: 25,
    total: 3,
    totalPages: 1,
  },
};

const summaryResponse: ReturnsSummary = {
  totalAsins: 3,
  totalUnits: 124,
  totalRefundAmount: 3719.49,
  avgRefundPerUnit: 29.99,
  topAsin: "B00-RET-003",
  topAsinRefundAmount: 1999.99,
};

type ReturnsStoryMode = {
  list: "default" | "empty" | "error" | "loading";
  stats: "default" | "loading";
};

const delayedResponse = (response: Response, delayMs = 2000) =>
  new Promise<Response>((resolve) => {
    setTimeout(() => resolve(response), delayMs);
  });

const buildHandlers = (mode: ReturnsStoryMode): FetchMockHandler[] => [
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/returns") && new URL(url).searchParams.get("resource") === "list",
    response: () => {
      if (mode.list === "error") {
        return new Response(JSON.stringify({ code: "BFF_ERROR", message: "Failed to load returns list." }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (mode.list === "empty") {
        return new Response(
          JSON.stringify({
            items: [],
            pagination: { page: 1, pageSize: 25, total: 0, totalPages: 1 },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      const payload = JSON.stringify(listResponse);
      const response = new Response(payload, { status: 200, headers: { "Content-Type": "application/json" } });
      return mode.list === "loading" ? delayedResponse(response) : response;
    },
  },
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/returns") && new URL(url).searchParams.get("resource") === "stats",
    response: () => {
      const payload = JSON.stringify(summaryResponse);
      const response = new Response(payload, { status: 200, headers: { "Content-Type": "application/json" } });
      return mode.stats === "loading" ? delayedResponse(response) : response;
    },
  },
];

const meta: Meta<typeof ReturnsPage> = {
  title: "Features/Returns/ReturnsPage",
  component: ReturnsPage,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof ReturnsPage>;

export const Default: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers({ list: "default", stats: "default" })}>
      <AppShell initialSession={mockSession} initialPath="/returns">
        <ReturnsPage />
      </AppShell>
    </FetchMock>
  ),
};

export const EmptyState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers({ list: "empty", stats: "default" })}>
      <AppShell initialSession={mockSession} initialPath="/returns">
        <ReturnsPage />
      </AppShell>
    </FetchMock>
  ),
};

export const LoadingState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers({ list: "loading", stats: "loading" })}>
      <AppShell initialSession={mockSession} initialPath="/returns">
        <ReturnsPage />
      </AppShell>
    </FetchMock>
  ),
};

export const ErrorState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers({ list: "error", stats: "default" })}>
      <AppShell initialSession={mockSession} initialPath="/returns">
        <ReturnsPage />
      </AppShell>
    </FetchMock>
  ),
};
