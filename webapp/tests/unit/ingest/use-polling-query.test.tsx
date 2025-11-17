import type { ReactElement } from "react";

import { act, render } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { usePollingQuery } from "@/lib/api/usePollingQuery";

type TestData = {
  state: string;
};

const renderWithClient = (ui: ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: 0,
      },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("usePollingQuery", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("polls until the stopWhen predicate returns true", async () => {
    let calls = 0;
    const queryFn = jest.fn().mockImplementation(() => {
      calls += 1;
      const state = calls >= 2 ? "done" : "pending";
      return Promise.resolve({ state });
    });

    const stopWhen = (data?: TestData) => data?.state === "done";

    const Harness = () => {
      usePollingQuery<TestData>({
        queryKey: ["polling", "stopWhen"],
        queryFn,
        stopWhen,
        pollingIntervalMs: 1000,
      });
      return null;
    };

    renderWithClient(<Harness />);

    expect(queryFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      jest.advanceTimersByTime(1000);
    });

    expect(queryFn).toHaveBeenCalledTimes(2);

    await act(async () => {
      jest.advanceTimersByTime(3000);
    });

    expect(queryFn).toHaveBeenCalledTimes(2);
  });

  it("stops polling after maxDurationMs is reached", async () => {
    const queryFn = jest.fn().mockResolvedValue({ state: "pending" });

    const Harness = () => {
      usePollingQuery<TestData>({
        queryKey: ["polling", "maxDuration"],
        queryFn,
        stopWhen: () => false,
        pollingIntervalMs: 500,
        maxDurationMs: 1500,
      });
      return null;
    };

    renderWithClient(<Harness />);

    expect(queryFn).toHaveBeenCalledTimes(1);

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(queryFn).toHaveBeenCalledTimes(3);

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(queryFn).toHaveBeenCalledTimes(3);
  });

  it("stops polling when the component unmounts", async () => {
    const queryFn = jest.fn().mockResolvedValue({ state: "pending" });

    const Harness = () => {
      usePollingQuery<TestData>({
        queryKey: ["polling", "unmount"],
        queryFn,
        stopWhen: () => false,
        pollingIntervalMs: 500,
      });
      return null;
    };

    const { unmount } = renderWithClient(<Harness />);

    await act(async () => {
      jest.advanceTimersByTime(500);
    });

    expect(queryFn).toHaveBeenCalledTimes(2);

    unmount();

    await act(async () => {
      jest.advanceTimersByTime(2000);
    });

    expect(queryFn).toHaveBeenCalledTimes(2);
  });
});
