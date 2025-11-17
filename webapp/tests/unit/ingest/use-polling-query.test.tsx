import { renderHook } from "@testing-library/react";

import { usePollingQuery } from "@/lib/api/usePollingQuery";

jest.mock("@/lib/api/useApiQuery", () => ({
  useApiQuery: jest.fn(),
}));

import { useApiQuery } from "@/lib/api/useApiQuery";

type TestData = {
  state: string;
};

const mockUseApiQuery = useApiQuery as jest.MockedFunction<typeof useApiQuery>;

describe("usePollingQuery", () => {
  beforeEach(() => {
    mockUseApiQuery.mockReset();
  });

  it("returns the polling interval until stopWhen is true", () => {
    let capturedInterval: ((query: { state: { data?: TestData }; dataUpdatedAt?: number }) => number | false) | null = null;
    const stopWhen = (data?: TestData) => data?.state === "done";

    mockUseApiQuery.mockImplementation((options) => {
      capturedInterval = options.refetchInterval as typeof capturedInterval;
      return {} as any;
    });

    const nowSpy = jest.spyOn(Date, "now");
    const baseTime = 1_000_000;
    nowSpy.mockReturnValue(baseTime);

    renderHook(() =>
      usePollingQuery<TestData>({
        queryKey: ["poll", "stop"],
        queryFn: jest.fn(),
        stopWhen,
        pollingIntervalMs: 1000,
      })
    );

    expect(capturedInterval).toBeTruthy();
    const intervalFn = capturedInterval!;
    expect(intervalFn({ state: { data: { state: "pending" } }, dataUpdatedAt: baseTime })).toBe(1000);
    expect(intervalFn({ state: { data: { state: "done" } }, dataUpdatedAt: baseTime })).toBe(false);

    nowSpy.mockRestore();
  });

  it("halts polling after maxDurationMs is exceeded", () => {
    let capturedInterval: ((query: { state: { data?: TestData }; dataUpdatedAt?: number }) => number | false) | null = null;
    const nowSpy = jest.spyOn(Date, "now");

    mockUseApiQuery.mockImplementation((options) => {
      capturedInterval = options.refetchInterval as typeof capturedInterval;
      return {} as any;
    });

    renderHook(() =>
      usePollingQuery<TestData>({
        queryKey: ["poll", "duration"],
        queryFn: jest.fn(),
        stopWhen: () => false,
        pollingIntervalMs: 500,
        maxDurationMs: 1500,
      })
    );

    expect(capturedInterval).toBeTruthy();
    const intervalFn = capturedInterval!;

    const baseTime = 5_000;
    nowSpy.mockReturnValue(baseTime);
    expect(intervalFn({ state: { data: { state: "pending" } }, dataUpdatedAt: baseTime })).toBe(500);

    nowSpy.mockReturnValue(baseTime + 2_000);
    expect(intervalFn({ state: { data: { state: "pending" } }, dataUpdatedAt: baseTime })).toBe(false);

    nowSpy.mockRestore();
  });

  it("returns false when polling is disabled", () => {
    let capturedInterval: ((query: { state: { data?: TestData }; dataUpdatedAt?: number }) => number | false) | null = null;

    mockUseApiQuery.mockImplementation((options) => {
      capturedInterval = options.refetchInterval as typeof capturedInterval;
      return {} as any;
    });

    renderHook(() =>
      usePollingQuery<TestData>({
        queryKey: ["poll", "disabled"],
        queryFn: jest.fn(),
        stopWhen: () => false,
        pollingIntervalMs: 1000,
        enabled: false,
      })
    );

    expect(capturedInterval).toBeTruthy();
    const intervalFn = capturedInterval!;
    expect(intervalFn({ state: { data: { state: "pending" } }, dataUpdatedAt: 0 })).toBe(false);
  });
});
