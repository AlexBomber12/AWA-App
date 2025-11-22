import type { ReactElement } from "react";

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { IngestJobForm } from "@/components/features/ingest/IngestJobForm";
import { startIngestJob } from "@/lib/api/ingestClient";

jest.mock("@/lib/api/ingestClient", () => ({
  startIngestJob: jest.fn(),
}));

const mockStartIngestJob = startIngestJob as jest.MockedFunction<typeof startIngestJob>;

const renderWithClient = (ui: ReactElement) => {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
};

describe("IngestJobForm", () => {
  const user = userEvent.setup();
  let consoleErrorSpy: jest.SpyInstance;

  beforeAll(() => {
    consoleErrorSpy = jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
  });

  beforeEach(() => {
    mockStartIngestJob.mockReset();
    consoleErrorSpy.mockClear();
  });

  it("submits an uploaded file and forwards the job payload", async () => {
    mockStartIngestJob.mockResolvedValue({
      task_id: "TASK-FILE",
      state: "PENDING",
      meta: {},
    });
    const onJobStarted = jest.fn();

    renderWithClient(<IngestJobForm onJobStarted={onJobStarted} />);

    const file = new File(["a,b\n1,2"], "roi.csv", { type: "text/csv" });
    await user.upload(screen.getByLabelText(/CSV or XLSX file/i), file);
    await user.click(screen.getByRole("button", { name: /Start ingest job/i }));

    await waitFor(() => expect(mockStartIngestJob).toHaveBeenCalledTimes(1));
    expect(mockStartIngestJob).toHaveBeenCalledWith(expect.objectContaining({ file }));
    expect(onJobStarted).toHaveBeenCalledWith(expect.objectContaining({ task_id: "TASK-FILE" }));
  });

  it("requires a valid URI when switched to remote mode", async () => {
    mockStartIngestJob.mockResolvedValue({
      task_id: "TASK-URI",
      state: "PENDING",
      meta: {},
    });

    renderWithClient(<IngestJobForm />);

    await user.click(screen.getByRole("tab", { name: /Remote URI/i }));
    await user.click(screen.getByRole("button", { name: /Start ingest job/i }));

    expect(await screen.findByText(/Enter the source URI to ingest/i)).toBeInTheDocument();

    const uriInput = screen.getByPlaceholderText(/s3:\/\/bucket\/path\/report\.csv/i);
    await user.clear(uriInput);
    await user.type(uriInput, "not-a-url");
    await user.click(screen.getByRole("button", { name: /Start ingest job/i }));

    expect(await screen.findByText(/Enter a valid URI/i)).toBeInTheDocument();
  });

  it("surfaces ApiErrors returned by the BFF", async () => {
    mockStartIngestJob.mockRejectedValue({
      code: "VALIDATION_ERROR",
      message: "Please fix the highlighted fields.",
      details: { fieldErrors: { uri: "Unsupported URI" } },
    });

    renderWithClient(<IngestJobForm />);

    await user.click(screen.getByRole("tab", { name: /Remote URI/i }));
    const uriInput = screen.getByPlaceholderText(/s3:\/\/bucket\/path\/report\.csv/i);
    await user.type(uriInput, "https://example.com/report.csv");
    await user.click(screen.getByRole("button", { name: /Start ingest job/i }));

    expect(await screen.findByText(/Please fix the highlighted fields/i)).toBeInTheDocument();
    expect(mockStartIngestJob).toHaveBeenCalled();
  });
});
