import { render, screen, waitFor, cleanup } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { UseQueryResult } from "@tanstack/react-query";

import { IngestJobStatus } from "@/components/features/ingest/IngestJobStatus";
import type { ApiError } from "@/lib/api/apiError";
import type { IngestJobStatus as IngestJobStatusType } from "@/lib/api/ingestClient";
import { usePollingQuery } from "@/lib/api/usePollingQuery";

jest.mock("@/lib/api/usePollingQuery", () => ({
  usePollingQuery: jest.fn(),
}));

const mockUsePollingQuery = usePollingQuery as jest.MockedFunction<typeof usePollingQuery>;

const defaultJob: IngestJobStatusType = {
  task_id: "TASK-123",
  state: "PENDING",
  meta: {},
};

type QueryResult = UseQueryResult<IngestJobStatusType, ApiError>;

const createQueryResult = (overrides: Partial<QueryResult> = {}): QueryResult => {
  const refetch = jest.fn().mockResolvedValue({ data: defaultJob });

  const base: Partial<QueryResult> = {
    data: defaultJob,
    error: null,
    isPending: false,
    isFetching: false,
    isError: false,
    isSuccess: true,
    status: "success",
    fetchStatus: "idle",
    dataUpdatedAt: Date.now(),
    errorUpdatedAt: 0,
    failureCount: 0,
    errorUpdateCount: 0,
    isLoading: false,
    isInitialLoading: false,
    isStale: false,
    isRefetching: false,
    refetch,
    remove: jest.fn(),
  };

  return {
    ...base,
    ...overrides,
  } as QueryResult;
};

type HookOptions = Parameters<typeof usePollingQuery>[0];

let lastOptions: HookOptions | null = null;
let consoleErrorSpy: jest.SpyInstance;

beforeAll(() => {
  consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
});

afterAll(() => {
  consoleErrorSpy.mockRestore();
});

beforeEach(() => {
  mockUsePollingQuery.mockReset();
  lastOptions = null;
});

afterEach(() => {
  cleanup();
  jest.clearAllMocks();
});

const renderComponent = (queryResult: QueryResult, uiProps?: Partial<React.ComponentProps<typeof IngestJobStatus>>) => {
  mockUsePollingQuery.mockImplementation((options) => {
    lastOptions = options;
    return queryResult;
  });

  const user = userEvent.setup();

  render(
    <IngestJobStatus
      taskId="TASK-123"
      initialStatus={defaultJob}
      pollingDisabled
      {...uiProps}
    />
  );

  return { user, queryResult };
};

const apiError: ApiError = {
  code: "BFF_ERROR",
  message: "temporarily unavailable",
  status: 502,
};

describe("IngestJobStatus", () => {
  it("renders success details and triggers manual refresh", async () => {
    const queryResult = createQueryResult({
      data: {
        task_id: "TASK-123",
        state: "SUCCESS",
        meta: { rows: 256, dialect: "returns_report", target_table: "returns_raw" },
      },
    });

    const { user } = renderComponent(queryResult);

    expect(screen.getByText(/Completed/i)).toBeInTheDocument();

    const rowsValue = screen.getByText(/Rows processed/i).nextSibling as HTMLElement | null;
    expect(rowsValue).not.toBeNull();
    expect(rowsValue as HTMLElement).toHaveTextContent("256");

    await user.click(screen.getByRole("button", { name: /Refresh/i }));
    expect(queryResult.refetch).toHaveBeenCalledTimes(1);
  });

  it("shows failure meta when the job reports an error", async () => {
    const queryResult = createQueryResult({
      data: {
        task_id: "TASK-123",
        state: "FAILURE",
        meta: { error: "ETL ingest failed" },
      },
    });

    renderComponent(queryResult);

    const [statusPill, description] = screen.getAllByText(/Failed/i);
    expect(statusPill).toBeInTheDocument();
    expect(description).toBeInTheDocument();
    expect(screen.getByText(/ETL ingest failed/)).toBeInTheDocument();
  });

  it("surfaces error banner and resume button after repeated polling errors", async () => {
    const queryResult = createQueryResult();
    const { user } = renderComponent(queryResult);

    lastOptions?.onError?.(apiError);
    lastOptions?.onError?.(apiError);
    lastOptions?.onError?.(apiError);

    await waitFor(() => expect(screen.getByText(/Unable to refresh job status/i)).toBeInTheDocument());

    const resumeButton = screen.getByRole("button", { name: /Resume polling/i });
    await user.click(resumeButton);

    expect(queryResult.refetch).toHaveBeenCalledTimes(1);
  });
});
