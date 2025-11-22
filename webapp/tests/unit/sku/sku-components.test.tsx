import { render, screen } from "@testing-library/react";

import { SkuCard } from "@/components/features/sku/SkuCard";
import { SkuPriceHistoryChart } from "@/components/features/sku/SkuPriceHistoryChart";
import type { SkuDetail } from "@/lib/api/skuClient";

const baseDetail: SkuDetail = {
  asin: "B00-DEMO-1",
  title: "Demo SKU",
  roi: 18.5,
  fees: 4.5,
  chartData: [
    { date: "2025-01-01T00:00:00Z", price: 12.5 },
    { date: "2025-01-05T00:00:00Z", price: 18.75 },
  ],
};

describe("SkuCard", () => {
  it("renders ROI, price delta, and snapshot details", () => {
    render(<SkuCard detail={baseDetail} />);

    expect(screen.getByText(/Demo SKU/)).toBeInTheDocument();
    expect(screen.getByText(/Action required/)).toBeInTheDocument();
    expect(screen.getByText(/Price vs first capture/)).toBeInTheDocument();
    expect(screen.getByText(/\$18\.75/)).toBeInTheDocument();
  });

  it("handles missing price history gracefully", () => {
    const noHistory: SkuDetail = { ...baseDetail, chartData: [], roi: 42, fees: 6.5 };

    render(<SkuCard detail={noHistory} />);

    expect(screen.getAllByText("–").length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByText(/Price vs first capture/)).not.toBeInTheDocument();
  });
});

describe("SkuPriceHistoryChart", () => {
  it("renders an empty state when history is missing", () => {
    render(<SkuPriceHistoryChart history={[]} />);

    expect(
      screen.getByText(/Price history is not available yet/i)
    ).toBeInTheDocument();
  });
});
