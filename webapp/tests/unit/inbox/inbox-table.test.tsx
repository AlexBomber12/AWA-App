import { render, screen, within } from "@testing-library/react";

import { InboxTable } from "@/components/features/inbox/InboxTable";
import type { Task } from "@/lib/api/inboxTypes";

const baseTask: Task = {
  id: "task-base",
  type: "ROI_REVIEW",
  title: "Base task",
  description: "Base description",
  status: "open",
  priority: "medium",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  summary: "Base summary",
  state: "open",
  source: "decision_engine",
};

const decisionTask: Task = {
  ...baseTask,
  id: "task-decision",
  summary: "Decision Task",
  priority: "high",
  decision: {
    decision: "update_price",
    priority: "high",
    defaultAction: "Raise price by 1%",
    why: ["ROI dipped"],
    alternatives: [],
  },
  entity: { type: "sku", asin: "B00-TEST-DECISION", sku: "TEST-DECISION", label: "Decision SKU" },
};

const fallbackTask: Task = {
  ...baseTask,
  id: "task-fallback",
  summary: "Fallback Task",
  priority: "low",
  decision: undefined,
  entity: undefined,
};

describe("InboxTable", () => {
  it("renders decision details when provided and falls back gracefully when missing", () => {
    render(<InboxTable tasks={[decisionTask, fallbackTask]} selectedTaskId={null} />);

    const table = screen.getByRole("table");

    const decisionRow = within(table).getByText(/Decision Task/).closest("tr");
    expect(decisionRow).toBeTruthy();
    if (decisionRow) {
      expect(within(decisionRow).getByText(/Raise price by 1%/i)).toBeInTheDocument();
      expect(within(decisionRow).getByText(/Decision SKU/)).toBeInTheDocument();
    }

    const fallbackRow = within(table).getByText(/Fallback Task/).closest("tr");
    expect(fallbackRow).toBeTruthy();
    if (fallbackRow) {
      expect(within(fallbackRow).getByText(/No decision/i)).toBeInTheDocument();
      expect(within(fallbackRow).getByText(/No entity/i)).toBeInTheDocument();
      expect(within(fallbackRow).getByText(/Open/i)).toBeInTheDocument();
    }
  });
});
