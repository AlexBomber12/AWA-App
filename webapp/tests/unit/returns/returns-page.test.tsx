import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { rest } from "msw";
import { setupServer } from "msw/node";
import type { ReactNode } from "react";

import { ReturnsPage } from "@/components/features/returns/ReturnsPage";
import type { ReturnsListResponse, ReturnsSummary } from "@/lib/api/returnsClient";

const user = userEvent.setup();

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
    usePathname: () => "/returns",
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

const buildListResponse = (page: number, pageSize: number): ReturnsListResponse => {
  const items = Array.from({ length: Math.min(pageSize, 5) }, (_, index) => {
    const asinNumber = (page - 1) * pageSize + index + 1;
    const asin = `RET-${asinNumber.toString().padStart(4, "0")}`;
    const qty = asinNumber * 2;
    const refundAmount = qty * 3.5;
    return {
      asin,
      qty,
      refundAmount,
      avgRefundPerUnit: 3.5,
    };
  });

  return {
    items,
    pagination: {
      page,
      pageSize,
      total: 50,
      totalPages: 2,
    },
  };
};

const summaryResponse: ReturnsSummary = {
  totalAsins: 50,
  totalUnits: 1200,
  totalRefundAmount: 42000,
  avgRefundPerUnit: 35,
  topAsin: "RET-0005",
  topAsinRefundAmount: 800,
};

const listCalls: string[] = [];

const server = setupServer(
  rest.get("http://localhost:3000/api/bff/returns", (req, res, ctx) => {
    const resource = req.url.searchParams.get("resource");
    if (resource === "stats") {
      return res(ctx.json(summaryResponse));
    }
    const page = Number(req.url.searchParams.get("page") ?? "1");
    const pageSize = Number(req.url.searchParams.get("page_size") ?? "25");
    listCalls.push(req.url.searchParams.toString());
    return res(ctx.json(buildListResponse(page, pageSize)));
  })
);

beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  listCalls.length = 0;
  const navigation = getNavigationMock();
  navigation.__internalNavigationMock.reset();
  navigation.__internalNavigationMock.setSearchParams("");
});
afterAll(() => server.close());

const renderWithClient = (ui: ReactNode) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("ReturnsPage", () => {
  it("loads returns data and updates pagination + filters", async () => {
    renderWithClient(<ReturnsPage />);

    await waitFor(() => expect(screen.getByText("RET-0001")).toBeInTheDocument());
    expect(listCalls.at(-1)).toContain("resource=list");

    await user.click(screen.getByRole("button", { name: /Next/i }));

    await waitFor(() => expect(screen.getByText("RET-0026")).toBeInTheDocument());
    expect(listCalls.at(-1)).toContain("page=2");

    const navigation = getNavigationMock();
    expect(navigation.__internalNavigationMock.getReplaceCalls().at(-1)).toContain("page=2");

    const vendorInput = screen.getByPlaceholderText("Vendor ID");
    await user.clear(vendorInput);
    await user.type(vendorInput, "ACME");
    await user.click(screen.getByRole("button", { name: /Apply filters/i }));

    await waitFor(() => expect(listCalls.at(-1)).toContain("filter%5Bvendor%5D=ACME"));
    expect(navigation.__internalNavigationMock.getReplaceCalls().at(-1)).toContain("filter%5Bvendor%5D=ACME");
  });

  it("renders navigation links for SKU and ROI", async () => {
    renderWithClient(<ReturnsPage />);

    const firstRow = await screen.findByText("RET-0001");
    const rowElement = firstRow.closest("tr");
    expect(rowElement).not.toBeNull();

    const asinLink = within(rowElement as HTMLElement).getByRole("link", { name: "RET-0001" });
    expect(asinLink).toHaveAttribute("href", "/sku/RET-0001?from=returns");

    const roiLink = within(rowElement as HTMLElement).getByRole("link", { name: /View in ROI/i });
    expect(roiLink).toHaveAttribute("href", "/roi?filter%5Bsearch%5D=RET-0001");
  });

  it("hydrates table state from existing query parameters", async () => {
    const navigation = getNavigationMock();
    navigation.__internalNavigationMock.setSearchParams("page=2&page_size=10&sort=qty_asc&filter%5Basin%5D=RET-0100");

    renderWithClient(<ReturnsPage />);

    await waitFor(() => expect(listCalls[0]).toBeDefined());
    expect(listCalls[0]).toContain("page=2");
    expect(listCalls[0]).toContain("page_size=10");
    expect(listCalls[0]).toContain("sort=qty_asc");
    expect(listCalls[0]).toContain("filter%5Basin%5D=RET-0100");
    await waitFor(() => expect(screen.getByText("RET-0011")).toBeInTheDocument());
  });
});
