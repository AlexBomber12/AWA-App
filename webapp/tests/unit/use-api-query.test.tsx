import type { ReactElement } from "react";

import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { rest } from "msw";
import { setupServer } from "msw/node";

import { statsClient } from "@/lib/api/statsClient";
import { useApiQuery } from "@/lib/api/useApiQuery";

const server = setupServer();

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const mockResponse = {
  kpi: { roi_avg: 45.8, products: 180, vendors: 11 },
  roiTrend: { points: [] },
};

const renderWithClient = (ui: ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("useApiQuery", () => {
  it("returns typed data when the request succeeds", async () => {
    server.use(
      rest.get("http://localhost:3000/api/bff/stats", (_req, res, ctx) => res(ctx.json(mockResponse)))
    );

    const TestComponent = () => {
      const { data, isSuccess } = useApiQuery({
        queryKey: ["dashboard", "stats", "kpi-success"],
        queryFn: () => statsClient.getKpi(),
        retry: 0,
      });

      if (isSuccess && data) {
        return (
          <div data-testid="kpi">
            ROI average {data.roi_avg} with {data.products} products
          </div>
        );
      }

      return <div data-testid="loading">Loading...</div>;
    };

    renderWithClient(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId("kpi")).toHaveTextContent("ROI average 45.8 with 180 products");
    });
  });

  it("exposes ApiErrors to consumers when the request fails", async () => {
    server.use(
      rest.get("http://localhost:3000/api/bff/stats", (_req, res, ctx) =>
        res(ctx.status(500), ctx.json({ code: "BFF_ERROR", message: "nope" }))
      )
    );

    const ErrorComponent = () => {
      const { error, isError } = useApiQuery({
        queryKey: ["dashboard", "stats", "kpi-error"],
        queryFn: () => statsClient.getKpi(),
        retry: 0,
      });

      if (isError && error) {
        return <div data-testid="error-message">{error.message}</div>;
      }

      return null;
    };

    renderWithClient(<ErrorComponent />);

    await waitFor(() => {
      expect(screen.getByTestId("error-message")).toHaveTextContent("nope");
    });
  });
});
