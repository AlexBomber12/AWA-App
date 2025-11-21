import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { rest } from "msw";
import { setupServer } from "msw/node";
import { type ReactNode, useState } from "react";

import { RoiTableContainer } from "@/components/features/roi/RoiTableContainer";

jest.mock("@/lib/api/fetchFromApi", () => ({
  fetchFromApi: jest.fn(),
  isApiError: () => false,
}));

const user = userEvent.setup();

jest.mock("@/components/features/roi/RoiTable", () => ({
  RoiTable: ({
    rows,
    page,
    onPageChange,
    onSelectRow,
    isLoading,
    onSortChange,
  }: {
    rows: Array<{ asin: string }>;
    page: number;
    onPageChange: (page: number) => void;
    onSelectRow: (asin: string, checked: boolean) => void;
    isLoading?: boolean;
    onSortChange: (sort: string) => void;
  }) => (
    <div data-testid="mock-roi-table">
      {isLoading ? <div>Loading…</div> : null}
      {rows.map((row) => (
        <div key={row.asin} className="flex items-center gap-2">
          <span>{row.asin}</span>
          <label>
            <input
              type="checkbox"
              aria-label={`Select ${row.asin}`}
              onChange={(event) => onSelectRow(row.asin, event.target.checked)}
            />
          </label>
        </div>
      ))}
      <button onClick={() => onPageChange(page + 1)}>Next</button>
      <button onClick={() => onSortChange("margin_desc")}>Sort margin</button>
    </div>
  ),
}));

jest.mock("@/components/features/roi/RoiFilters", () => ({
  RoiFilters: ({
    onApply,
    onReset,
  }: {
    onApply: (filters: { vendor?: string }) => void;
    onReset: () => void;
  }) => (
    <div data-testid="roi-filters">
      <button onClick={() => onApply({ vendor: "42" })}>Apply vendor 42</button>
      <button onClick={() => onReset()}>Reset filters</button>
    </div>
  ),
}));

jest.mock("next/navigation", () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require("react");
  let searchParams = new URLSearchParams();
  const listeners = new Set<() => void>();
  const routerReplace = jest.fn((url: string) => {
    const [, query = ""] = url.split("?");
    searchParams = new URLSearchParams(query);
    listeners.forEach((listener) => listener());
  });

  const subscribe = (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  return {
    usePathname: () => "/roi",
    useRouter: () => ({ replace: routerReplace }),
    useSearchParams: () => {
      const [, forceRender] = React.useState(0);
      React.useEffect(() => {
        const notify = () => forceRender((value: number) => value + 1);
        return subscribe(notify);
      }, []);
      return searchParams;
    },
    __internalNavigationMock: {
      setSearchParams: (query: string) => {
        searchParams = new URLSearchParams(query);
        listeners.forEach((listener) => listener());
      },
      getReplaceCalls: () => routerReplace.mock.calls.map(([url]: [string]) => url),
      reset: () => routerReplace.mockClear(),
    },
  };
});

const getNavigationMock = () =>
  require("next/navigation") as {
    __internalNavigationMock: {
      setSearchParams: (query: string) => void;
      getReplaceCalls: () => string[];
      reset: () => void;
    };
  };

type RoiListResponse = {
  items: Array<{
    asin: string;
    title: string;
    vendor_id: number;
    category: string;
    cost: number;
    freight: number;
    fees: number;
    roi_pct: number;
  }>;
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
};

const buildResponse = (page: number, pageSize: number): RoiListResponse => {
  const items = Array.from({ length: pageSize }, (_, index) => {
    const asinNum = (page - 1) * pageSize + index + 1;
    return {
      asin: `ASIN-${asinNum.toString().padStart(4, "0")}`,
      title: `Demo SKU ${asinNum}`,
      vendor_id: (asinNum % 5) + 1,
      category: asinNum % 2 === 0 ? "Beauty" : "Outdoors",
      cost: 10 + asinNum,
      freight: 2,
      fees: 1.5,
      roi_pct: 20 + asinNum,
    };
  });

  return {
    items,
    pagination: {
      page,
      pageSize,
      total: 120,
      totalPages: 3,
    },
  };
};

const getCalls: string[] = [];
const approvePayloads: Array<{ asins: string[] }> = [];

const server = setupServer(
  rest.get("http://localhost:3000/api/bff/roi", (req, res, ctx) => {
    const page = Number(req.url.searchParams.get("page") ?? "1");
    const pageSize = Number(req.url.searchParams.get("page_size") ?? "50");
    getCalls.push(req.url.searchParams.toString());
    return res(ctx.json(buildResponse(page, pageSize)));
  }),
  rest.post("http://localhost:3000/api/bff/roi/bulk-approve", async (req, res, ctx) => {
    const body = (await req.json()) as { asins: string[] };
    approvePayloads.push(body);
    return res(
      ctx.json({
        updated: body.asins.length,
        approved_ids: body.asins,
      })
    );
  })
);

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  getCalls.length = 0;
  approvePayloads.length = 0;
  const navigation = getNavigationMock();
  navigation.__internalNavigationMock.reset();
  navigation.__internalNavigationMock.setSearchParams("");
});
afterAll(() => server.close());

const renderWithClient = (ui: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

const RoiHarness = () => {
  const [actions, setActions] = useState<ReactNode | null>(null);
  return (
    <>
      <div data-testid="actions">{actions}</div>
      <RoiTableContainer canApprove={true} onActionsChange={setActions} />
    </>
  );
};

describe("RoiTableContainer integration", () => {
  it("loads ROI rows, updates pagination, and performs bulk approval via BFF", async () => {
    renderWithClient(<RoiHarness />);

    await waitFor(() => expect(screen.getByText("ASIN-0001")).toBeInTheDocument());
    expect(getCalls.length).toBe(1);

    await user.click(screen.getByRole("button", { name: /Next/i }));
    await waitFor(() => expect(screen.getByText("ASIN-0051")).toBeInTheDocument());

    const navigation = getNavigationMock();
    expect(navigation.__internalNavigationMock.getReplaceCalls().at(-1)).toContain("page=2");

    const checkbox = await screen.findByLabelText("Select ASIN-0051");
    await user.click(checkbox);

    const bulkButton = screen.getByRole("button", { name: /Bulk approve/i });
    expect(bulkButton).not.toBeDisabled();
    await user.click(bulkButton);

    await waitFor(() => expect(screen.getByText(/Bulk approve selection/i)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Approve selection/i }));

    await waitFor(() => expect(approvePayloads).toHaveLength(1));
    expect(approvePayloads[0]).toEqual({ asins: ["ASIN-0051"] });
    await waitFor(() => expect(screen.queryByText(/Bulk approve selection/i)).not.toBeInTheDocument());

    await waitFor(() => expect(screen.getByRole("button", { name: /Bulk approve/i })).toBeDisabled());
    expect(getCalls.length).toBeGreaterThanOrEqual(2);
  });

  it("applies filters and sort changes via query params", async () => {
    renderWithClient(<RoiHarness />);

    await waitFor(() => expect(screen.getByText("ASIN-0001")).toBeInTheDocument());

    await user.click(screen.getByText("Apply vendor 42"));
    await waitFor(() => expect(getCalls.at(-1)).toContain("filter%5Bvendor%5D=42"));

    await user.click(screen.getByText("Sort margin"));
    await waitFor(() => expect(getCalls.at(-1)).toContain("sort=margin_desc"));
  });

  it("hydrates table state from URL search params", async () => {
    const navigation = getNavigationMock();
    navigation.__internalNavigationMock.setSearchParams(
      "page=3&page_size=25&sort=asin_desc&filter%5Bvendor%5D=88"
    );

    renderWithClient(<RoiHarness />);

    await waitFor(() => expect(getCalls[0]).toBeDefined());
    expect(getCalls[0]).toContain("page=3");
    expect(getCalls[0]).toContain("page_size=25");
    expect(getCalls[0]).toContain("sort=asin_desc");
    expect(getCalls[0]).toContain("filter%5Bvendor%5D=88");
    await waitFor(() => expect(screen.getByText("ASIN-0051")).toBeInTheDocument());
  });
});
