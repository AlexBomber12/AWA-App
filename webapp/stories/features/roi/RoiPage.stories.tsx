import type { Meta, StoryObj } from "@storybook/react";
import { expect, userEvent, waitFor, within } from "@storybook/test";
import type { Session } from "next-auth";

import { RoiPage } from "@/components/features/roi/RoiPage";
import {
  ROI_TABLE_DEFAULTS,
  mergeRoiTableStateWithDefaults,
  parseRoiSearchParams,
  type RoiSort,
  type RoiTableFilters,
} from "@/components/features/roi/tableState";
import type { RoiListResponse, RoiRow } from "@/components/features/roi/types";
import { AppShell } from "@/components/layout";

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

const OBSERVE_ONLY_ROI_THRESHOLD = 20;

const createRoiRow = (index: number): RoiRow => ({
  asin: `ROI-${(index + 1).toString().padStart(4, "0")}`,
  title: `Storybook ROI SKU ${index + 1}`,
  vendor_id: (index % 9) + 1,
  category: ["Beauty", "Electronics", "Outdoors"][index % 3],
  cost: 10 + (index % 5),
  freight: 2 + (index % 3),
  fees: 1.5 + (index % 4),
  roi_pct: 12 + (index % 35),
});

const MOCK_ROWS: RoiRow[] = Array.from({ length: 150 }, (_, index) => createRoiRow(index));

const marginValue = (row: RoiRow): number => {
  const roiPct = row.roi_pct ?? 0;
  const cost = (row.cost ?? 0) + (row.freight ?? 0) + (row.fees ?? 0);
  return (roiPct / 100) * cost;
};

const matchesFilters = (row: RoiRow, filters: RoiTableFilters): boolean => {
  const roiMin = typeof filters.roiMin === "number" ? filters.roiMin : 0;
  const vendor = filters.vendor?.trim();
  const category = filters.category?.trim().toLowerCase();
  const search = filters.search?.trim().toLowerCase();
  const observeOnly = Boolean(filters.observeOnly);

  if ((row.roi_pct ?? 0) < roiMin) {
    return false;
  }
  if (observeOnly && (row.roi_pct ?? 0) > OBSERVE_ONLY_ROI_THRESHOLD) {
    return false;
  }
  if (vendor && String(row.vendor_id ?? "") !== vendor) {
    return false;
  }
  if (category && (row.category ?? "").toLowerCase() !== category) {
    return false;
  }
  if (search) {
    const haystack = `${row.asin ?? ""} ${row.title ?? ""}`.toLowerCase();
    if (!haystack.includes(search)) {
      return false;
    }
  }
  return true;
};

const sortRows = (rows: RoiRow[], sort: RoiSort | undefined) => {
  const next = [...rows];
  switch (sort) {
    case "roi_pct_asc":
      return next.sort((a, b) => (a.roi_pct ?? 0) - (b.roi_pct ?? 0));
    case "asin_asc":
      return next.sort((a, b) => (a.asin ?? "").localeCompare(b.asin ?? ""));
    case "asin_desc":
      return next.sort((a, b) => (b.asin ?? "").localeCompare(a.asin ?? ""));
    case "margin_asc":
      return next.sort((a, b) => marginValue(a) - marginValue(b));
    case "margin_desc":
      return next.sort((a, b) => marginValue(b) - marginValue(a));
    case "vendor_asc":
      return next.sort((a, b) => (a.vendor_id ?? 0) - (b.vendor_id ?? 0));
    case "vendor_desc":
      return next.sort((a, b) => (b.vendor_id ?? 0) - (a.vendor_id ?? 0));
    case "roi_pct_desc":
    default:
      return next.sort((a, b) => (b.roi_pct ?? 0) - (a.roi_pct ?? 0));
  }
};

const buildRoiHandlers = (): FetchMockHandler[] => [
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/roi") && !url.includes("/bulk-approve"),
    response: ({ url }) => {
      const params = new URL(url).searchParams;
      const state = mergeRoiTableStateWithDefaults(parseRoiSearchParams(params));
      const filters = state.filters ?? ROI_TABLE_DEFAULTS.filters ?? {};
      const filtered = MOCK_ROWS.filter((row) => matchesFilters(row, filters));
      const sortKey = state.sort ?? ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc";
      const sorted = sortRows(filtered, sortKey);
      const total = sorted.length;
      const totalPages = Math.max(1, Math.ceil(total / state.pageSize));
      const safePage = Math.min(state.page, totalPages);
      const start = (safePage - 1) * state.pageSize;
      const items = sorted.slice(start, start + state.pageSize);
      const response: RoiListResponse = {
        items,
        pagination: {
          page: safePage,
          pageSize: state.pageSize,
          total,
          totalPages,
        },
      };
      return new Response(JSON.stringify(response), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    },
  },
  {
    predicate: ({ url, method }) => method === "POST" && url.includes("/api/bff/roi/bulk-approve"),
    response: async ({ init }) => {
      let asins: string[] = [];
      if (init?.body && typeof init.body === "string") {
        try {
          const payload = JSON.parse(init.body) as { asins?: string[] };
          asins = payload.asins ?? [];
        } catch {
          asins = [];
        }
      }
      return new Response(
        JSON.stringify({
          updated: asins.length,
          approved_ids: asins,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } }
      );
    },
  },
];

const meta: Meta<typeof RoiPage> = {
  title: "Features/ROI/RoiPage",
  component: RoiPage,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof RoiPage>;

const renderWithMocks = () => (
  <FetchMock handlers={buildRoiHandlers()}>
    <AppShell initialSession={mockSession} initialPath="/roi">
      <RoiPage />
    </AppShell>
  </FetchMock>
);

export const Default: Story = {
  render: () => renderWithMocks(),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const user = userEvent.setup();
    await waitFor(() => expect(canvas.getByText("ROI-0001")).toBeInTheDocument());

    await user.click(canvas.getByRole("button", { name: /Next/i }));
    await waitFor(() => expect(canvas.getByText("ROI-0051")).toBeInTheDocument());

    await user.click(canvas.getByRole("button", { name: "SKU" }));
    await user.click(canvas.getByRole("button", { name: /Vendor/i }));

    const searchInput = canvas.getByPlaceholderText("Find ASIN or title");
    const vendorInput = canvas.getByPlaceholderText("Vendor");
    await user.clear(searchInput);
    await user.type(searchInput, "ROI-0003");
    await user.clear(vendorInput);
    await user.type(vendorInput, "2");

    await user.click(canvas.getByRole("button", { name: /Apply filters/i }));
    await waitFor(() => expect(canvas.getByText("ROI-0003")).toBeInTheDocument());
  },
};
