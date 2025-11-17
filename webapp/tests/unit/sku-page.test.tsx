import { render, screen } from "@testing-library/react";

import { SkuPage } from "@/components/features/sku/SkuPage";
import { type SkuDetail, useSkuDetailQuery } from "@/lib/api/skuClient";

jest.mock("@/lib/api/skuClient", () => ({
  useSkuDetailQuery: jest.fn(),
}));

const mockUseSkuDetailQuery = useSkuDetailQuery as jest.MockedFunction<typeof useSkuDetailQuery>;

const mockDetail: SkuDetail = {
  asin: "B00-PAGE-001",
  title: "Unit Test Hydration Pack",
  roi: 44.2,
  fees: 10.5,
  chartData: [
    { date: "2025-02-10T00:00:00Z", price: 32.2 },
    { date: "2025-02-11T00:00:00Z", price: 34.9 },
  ],
};

beforeEach(() => {
  mockUseSkuDetailQuery.mockReset();
});

describe("SkuPage", () => {
  it("renders the summary card and chart when data is loaded", () => {
    mockUseSkuDetailQuery.mockReturnValue({
      data: mockDetail,
      isPending: false,
      error: null,
      refetch: jest.fn(),
    } as any);

    render(<SkuPage asin="B00-PAGE-001" fetchEnabled={false} initialData={mockDetail} />);

    expect(screen.getByText(/SKU snapshot/i)).toBeInTheDocument();
    expect(screen.getByText(/Unit Test Hydration Pack/)).toBeInTheDocument();
    expect(screen.getByText(/Return on investment/i)).toBeInTheDocument();
    expect(screen.getByText(/Price & ROI history/i)).toBeInTheDocument();
  });

  it("shows a loading skeleton while the query is pending", () => {
    mockUseSkuDetailQuery.mockReturnValue({
      data: undefined,
      isPending: true,
      error: null,
      refetch: jest.fn(),
    } as any);

    render(<SkuPage asin="B00-PAGE-002" />);

    expect(screen.getByTestId("sku-page-skeleton")).toBeInTheDocument();
  });

  it("renders an error state when the query fails", () => {
    mockUseSkuDetailQuery.mockReturnValue({
      data: undefined,
      isPending: false,
      error: { message: "boom" },
      refetch: jest.fn(),
    } as any);

    render(<SkuPage asin="B00-PAGE-003" />);

    expect(screen.getByText(/Unable to load SKU detail/)).toBeInTheDocument();
  });

  it("renders a contextual backlink based on the source route", () => {
    mockUseSkuDetailQuery.mockReturnValue({
      data: mockDetail,
      isPending: false,
      error: null,
      refetch: jest.fn(),
    } as any);

    render(<SkuPage asin="B00-PAGE-004" from="roi" fetchEnabled={false} initialData={mockDetail} />);

    expect(screen.getByRole("link", { name: /Back to ROI/ })).toBeInTheDocument();
  });
});
