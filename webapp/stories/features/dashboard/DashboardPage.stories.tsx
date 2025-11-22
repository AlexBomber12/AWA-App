import type { Meta, StoryObj } from "@storybook/react";

import { DashboardPageClient } from "@/components/features/dashboard/DashboardPageClient";
import { AppShell, PageBody, PageHeader } from "@/components/layout";
import type { StatsKpi } from "@/lib/api/statsClient";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

const mockKpi: StatsKpi = {
  roi_avg: 42.5,
  products: 184,
  vendors: 16,
};

const mockTrend = {
  points: [
    { month: "2024-01-01", roi_avg: 36, items: 120 },
    { month: "2024-02-01", roi_avg: 39, items: 132 },
    { month: "2024-03-01", roi_avg: 44, items: 148 },
    { month: "2024-04-01", roi_avg: 45, items: 153 },
  ],
};

type DashboardStoryMode = "default" | "loading" | "error";

const delayedResponse = (response: Response, delayMs = 1200) =>
  new Promise<Response>((resolve) => setTimeout(() => resolve(response), delayMs));

const buildHandlers = (mode: DashboardStoryMode): FetchMockHandler[] => [
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/stats"),
    response: () => {
      if (mode === "error") {
        return new Response(JSON.stringify({ code: "BFF_ERROR", message: "Unable to load dashboard stats." }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        });
      }
      const payload = new Response(
        JSON.stringify({
          kpi: mockKpi,
          roiTrend: mockTrend,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
      return mode === "loading" ? delayedResponse(payload) : payload;
    },
  },
];

const meta: Meta<typeof DashboardPageClient> = {
  title: "Features/Dashboard/DashboardPage",
  component: DashboardPageClient,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof DashboardPageClient>;

const renderWithShell = (mode: DashboardStoryMode) => (
  <FetchMock handlers={buildHandlers(mode)}>
    <AppShell initialSession={{ user: { name: "Story Admin", email: "ops@example.com", roles: ["admin"] }, expires: "" }} initialPath="/dashboard">
      <PageHeader
        title="Dashboard"
        description="Live KPIs and ROI trajectories for the ingestion pipeline."
        breadcrumbs={[{ label: "Dashboard", href: "/dashboard", active: true }]}
      />
      <PageBody>
        <DashboardPageClient />
      </PageBody>
    </AppShell>
  </FetchMock>
);

export const Default: Story = {
  render: () => renderWithShell("default"),
};

export const Loading: Story = {
  render: () => renderWithShell("loading"),
};

export const ErrorState: Story = {
  render: () => renderWithShell("error"),
};
