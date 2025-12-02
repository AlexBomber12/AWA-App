import { render, screen } from "@testing-library/react";

import { TaskDetailsDrawer } from "@/components/features/inbox/TaskDetailsDrawer";
import { PermissionsProvider } from "@/lib/permissions/client";
import type { Task } from "@/lib/api/inboxTypes";
import { SessionProvider } from "next-auth/react";

const baseTask: Task = {
  id: "task-detail",
  type: "DECISION_TASK",
  title: "Decision Task",
  description: "Review the decision recommendation",
  status: "open",
  priority: "high",
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  summary: "Check margin guardrail",
  state: "open",
  source: "decision_engine",
  entity: { type: "sku", asin: "B00-DETAIL", label: "Detail SKU" },
  decision: {
    decision: "update_price",
    priority: "high",
    defaultAction: "Raise price now",
    why: ["Margin below target"],
    alternatives: [{ decision: "wait_until", label: "Re-evaluate in 24h" }],
    metrics: { roi: 12.5, riskAdjustedRoi: 10.4, maxCogs: 14.8 },
  },
};

const renderWithPermissions = (task: Task) =>
  render(
    <SessionProvider session={{ user: { name: "Admin", email: "admin@example.com", roles: ["admin"] }, expires: "" }}>
      <PermissionsProvider roles={["admin"]}>
        <TaskDetailsDrawer
          task={task}
          isOpen
          onClose={() => undefined}
          onApply={() => undefined}
          onDecline={() => undefined}
          onSnooze={() => undefined}
          canUndo
          onUndo={() => undefined}
        />
      </PermissionsProvider>
    </SessionProvider>
  );

describe("TaskDetailsDrawer", () => {
  it("renders decision details and metrics when provided", () => {
    renderWithPermissions(baseTask);

    expect(screen.getByText(/Check margin guardrail/i)).toBeInTheDocument();
    expect(screen.getByText(/Raise price now/i)).toBeInTheDocument();
    expect(screen.getByText(/Risk-adjusted ROI/i)).toBeInTheDocument();
    expect(screen.getByText(/Max COGS/i)).toBeInTheDocument();
  });

  it("handles missing metrics and optional fields gracefully", () => {
    const withoutMetrics: Task = {
      ...baseTask,
      id: "task-no-metrics",
      summary: "No metrics task",
      decision: {
        decision: "continue",
        priority: "medium",
        why: [],
        alternatives: [],
      },
      entity: undefined,
      priority: undefined,
      state: undefined,
    };

    renderWithPermissions(withoutMetrics);

    expect(screen.getByText(/No metrics task/i)).toBeInTheDocument();
    expect(screen.queryByText(/ROI/)).not.toBeInTheDocument();
    expect(screen.getByText(/No entity/i)).toBeInTheDocument();
    expect(screen.getByText(/Open/i)).toBeInTheDocument();
  });
});
