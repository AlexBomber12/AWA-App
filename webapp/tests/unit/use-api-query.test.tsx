import { type ReactElement, useState } from "react";

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { rest } from "msw";
import { setupServer } from "msw/node";

import { statsClient } from "@/lib/api/statsClient";
import { useApiQuery } from "@/lib/api/useApiQuery";

const server = setupServer();
const user = userEvent.setup();

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

  it("respects the enabled flag before firing the query", async () => {
    const queryFn = jest.fn().mockResolvedValue({ alpha: 1 });

    const Harness = () => {
      const [enabled, setEnabled] = useState(false);
      const { data } = useApiQuery({
        queryKey: ["test", "enabled"],
        queryFn,
        enabled,
      });

      return (
        <div>
          <button onClick={() => setEnabled(true)}>Enable</button>
          <span data-testid="status">{data ? "loaded" : "idle"}</span>
        </div>
      );
    };

    renderWithClient(<Harness />);

    expect(queryFn).not.toHaveBeenCalled();
    await user.click(screen.getByText("Enable"));
    await waitFor(() => expect(queryFn).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("loaded"));
  });

  it("invokes the onError callback when the query fails", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    server.use(
      rest.get("http://localhost:3000/api/bff/stats", (_req, res, ctx) =>
        res(ctx.status(500), ctx.json({ code: "BFF_ERROR", message: "boom" }))
      )
    );
    const onError = jest.fn();

    const ErrorHarness = () => {
      useApiQuery({
        queryKey: ["dashboard", "stats", "kpi-onerror"],
        queryFn: () => statsClient.getKpi(),
        retry: 0,
        onError,
      });
      return null;
    };

    renderWithClient(<ErrorHarness />);

    await waitFor(() => expect(onError).toHaveBeenCalledTimes(1));
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
