import type { Meta, StoryObj } from "@storybook/react";
import { expect, userEvent, waitFor, within } from "@storybook/test";
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

const formatAsin = (value: number) => `B00-RET-${value.toString().padStart(3, "0")}`;

const buildDefaultListPayload = (pageParam: number, pageSizeParam: number): ReturnsListResponse => {
  const total = 60;
  const pageSize = Math.max(1, pageSizeParam);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const page = Math.min(Math.max(pageParam, 1), totalPages);
  const startIndex = (page - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, total);

  const items = Array.from({ length: endIndex - startIndex }, (_, index) => {
    const id = startIndex + index + 1;
    return {
      asin: formatAsin(id),
      qty: id * 2,
      refundAmount: id * 25,
      avgRefundPerUnit: 25,
    };
  });

  return {
    items,
    pagination: {
      page,
      pageSize,
      total,
      totalPages,
    },
  };
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
    response: ({ url }) => {
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
      const params = new URL(url).searchParams;
      const page = Number(params.get("page") ?? "1");
      const pageSize = Number(params.get("page_size") ?? "25");
      const payload = JSON.stringify(buildDefaultListPayload(page, pageSize));
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

export const InteractiveTable: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers({ list: "default", stats: "default" })}>
      <AppShell initialSession={mockSession} initialPath="/returns">
        <ReturnsPage />
      </AppShell>
    </FetchMock>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const user = userEvent.setup();

    await waitFor(() => expect(canvas.getByText("B00-RET-001")).toBeInTheDocument());

    await user.click(canvas.getByRole("button", { name: /Next/i }));
    await waitFor(() => expect(canvas.getByText("B00-RET-026")).toBeInTheDocument());

    const vendorInput = canvas.getByPlaceholderText("Vendor ID");
    await user.clear(vendorInput);
    await user.type(vendorInput, "ACME");

    await user.click(canvas.getByRole("button", { name: /Apply filters/i }));
    await waitFor(() => expect(canvas.getByRole("button", { name: /Previous/i })).not.toBeDisabled());
  },
};
