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

const handlers: FetchMockHandler[] = [
  {
    predicate: ({ url, method }) => {
      if (method !== "GET" || !url.includes("/api/bff/returns")) {
        return false;
      }
      const resource = new URL(url).searchParams.get("resource");
      return resource === "list";
    },
    response: () =>
      new Response(JSON.stringify(listResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
  },
  {
    predicate: ({ url, method }) => {
      if (method !== "GET" || !url.includes("/api/bff/returns")) {
        return false;
      }
      const resource = new URL(url).searchParams.get("resource");
      return resource === "stats";
    },
    response: () =>
      new Response(JSON.stringify(summaryResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
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
    <FetchMock handlers={handlers}>
      <AppShell initialSession={mockSession} initialPath="/returns">
        <ReturnsPage />
      </AppShell>
    </FetchMock>
  ),
};
