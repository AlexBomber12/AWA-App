import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

import { IngestPage } from "@/components/features/ingest/IngestPage";
import type { IngestJobStatus as IngestJobStatusType } from "@/lib/api/ingestClient";
import { usePermissions } from "@/lib/permissions";

jest.mock("@/components/features/ingest/IngestJobForm", () => ({
  IngestJobForm: ({ onJobStarted, disabled }: { onJobStarted?: (job: IngestJobStatusType) => void; disabled?: boolean }) => (
    <div>
      <button disabled={disabled} onClick={() => onJobStarted?.({ task_id: "TASK-MOCK", state: "PENDING", meta: {} })}>
        Mock submit
      </button>
    </div>
  ),
}));

jest.mock("@/components/features/ingest/IngestJobStatus", () => ({
  IngestJobStatus: ({ taskId }: { taskId: string }) => <div data-testid="job-card">Job {taskId}</div>,
}));

jest.mock("@/lib/permissions", () => ({
  usePermissions: jest.fn(),
}));

const mockedPermissions = usePermissions as jest.MockedFunction<typeof usePermissions>;

describe("IngestPage", () => {
  const user = userEvent.setup();

  beforeEach(() => {
    mockedPermissions.mockReturnValue({
      roles: ["ops"],
      can: () => true,
      hasRole: () => true,
    });
  });

  it("adds a job card when the form reports success", async () => {
    render(<IngestPage />);

    await user.click(screen.getByRole("button", { name: /Mock submit/i }));

    expect(screen.getByTestId("job-card")).toHaveTextContent("TASK-MOCK");
  });

  it("blocks the form when the user lacks ingest permissions", () => {
    mockedPermissions.mockReturnValue({
      roles: ["viewer"],
      can: () => false,
      hasRole: () => false,
    });

    render(<IngestPage />);

    expect(screen.getByText(/do not have permission/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mock submit/i })).toBeDisabled();
  });
});
