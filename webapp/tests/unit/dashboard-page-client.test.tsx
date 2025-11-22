import { render, screen } from "@testing-library/react";

import { DashboardPageClient } from "@/components/features/dashboard/DashboardPageClient";
import { type StatsKpi } from "@/lib/api/statsClient";

jest.mock("@/lib/api/useApiQuery", () => ({
  useApiQuery: jest.fn(),
}));

const mockUseApiQuery = jest.requireMock("@/lib/api/useApiQuery")
  .useApiQuery as jest.MockedFunction<any>;

const mockKpi: StatsKpi = {
  roi_avg: 41.5,
  products: 142,
  vendors: 9,
};

const mockTrend = {
  points: [
    { month: "2024-01-01", roi_avg: 38.4, items: 40 },
    { month: "2024-02-01", roi_avg: 42.8, items: 44 },
  ],
};

describe("DashboardPageClient", () => {
  beforeEach(() => {
    mockUseApiQuery.mockReset();
    mockUseApiQuery
      .mockReturnValueOnce({
        data: mockKpi,
        isPending: false,
        error: null,
        refetch: jest.fn(),
      })
      .mockReturnValueOnce({
        data: mockTrend,
        isPending: false,
        error: null,
        refetch: jest.fn(),
      });
  });

  it("matches the dashboard snapshot for a populated state", () => {
    const { asFragment } = render(<DashboardPageClient />);

    expect(asFragment()).toMatchSnapshot();
  });

  it("renders KPI error state and ROI skeleton when loading", () => {
    mockUseApiQuery.mockReset();
    mockUseApiQuery
      .mockReturnValueOnce({
        data: undefined,
        isPending: false,
        error: new Error("kpi failed"),
        refetch: jest.fn(),
      })
      .mockReturnValueOnce({
        data: undefined,
        isPending: true,
        error: null,
        refetch: jest.fn(),
      });

    const { container } = render(<DashboardPageClient />);

    expect(screen.getByText(/Unable to load KPIs/i)).toBeInTheDocument();
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("shows ROI error when the trend query fails", () => {
    mockUseApiQuery.mockReset();
    mockUseApiQuery
      .mockReturnValueOnce({
        data: mockKpi,
        isPending: false,
        error: null,
        refetch: jest.fn(),
      })
      .mockReturnValueOnce({
        data: undefined,
        isPending: false,
        error: new Error("roi failed"),
        refetch: jest.fn(),
      });

    render(<DashboardPageClient />);

    expect(screen.getByText(/Unable to load ROI trend/i)).toBeInTheDocument();
  });
});
