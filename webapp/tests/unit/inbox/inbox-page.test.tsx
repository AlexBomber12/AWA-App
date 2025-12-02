import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { rest } from "msw";
import { setupServer } from "msw/node";
import type { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";
import type { ReactNode } from "react";

import { InboxPage } from "@/components/features/inbox/InboxPage";
import { ToastProvider } from "@/components/providers/ToastProvider";
import type { InboxListResponse } from "@/lib/api/inboxClient";
import type { Task } from "@/lib/api/inboxTypes";

jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: jest.fn(), push: jest.fn() }),
}));

const user = userEvent.setup();

const inboxItems: Task[] = [
  {
    id: "test-task-1",
    source: "decision_engine",
    entity: { type: "sku_vendor", asin: "B00TEST1", vendorId: "22", label: "Test SKU 1" },
    summary: "Review mock decision",
    assignee: "Ops User",
    state: "open",
    decision: {
      decision: "update_price",
      priority: "high",
      deadlineAt: new Date().toISOString(),
      defaultAction: "Increase price by 1%",
      why: ["ROI dipped below guardrail"],
      alternatives: [{ decision: "request_discount", label: "Request discount" }],
      metrics: { roi: 12.1, riskAdjustedRoi: 10.2, maxCogs: 14.5 },
    },
    priority: "high",
    deadlineAt: new Date().toISOString(),
    why: ["ROI dipped below guardrail"],
    alternatives: [{ decision: "request_discount", label: "Request discount" }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

const inboxResponse: InboxListResponse = {
  data: inboxItems,
  items: inboxItems,
  pagination: { page: 1, pageSize: 25, total: 1, totalPages: 1 },
  summary: { open: 1, inProgress: 0, blocked: 0 },
};

const server = setupServer(
  rest.get("http://localhost:3000/api/bff/inbox", (_req, res, ctx) => {
    return res(ctx.json(inboxResponse));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Test User",
    email: "ops@example.com",
    roles,
  },
  expires: "",
});

const renderWithProviders = (ui: ReactNode, roles: string[] = ["ops"]) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <SessionProvider session={buildSession(roles)}>
      <ToastProvider>
        <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
      </ToastProvider>
    </SessionProvider>
  );
};

describe("InboxPage", () => {
  it("loads tasks and opens the drawer on row click", async () => {
    renderWithProviders(<InboxPage />);

    const table = await screen.findByRole("table");
    const summaryCell = within(table).getByText("Review mock decision");
    await user.click(summaryCell);

    const drawer = await screen.findByRole("dialog");
    expect(within(drawer).getByRole("heading", { name: /Review mock decision/i })).toBeInTheDocument();
    expect(within(drawer).getAllByText(/update price/i).length).toBeGreaterThan(0);
    expect(within(drawer).getByText(/ROI dipped below guardrail/i)).toBeInTheDocument();
  });

  it("snoozes a task optimistically and undo restores the previous state", async () => {
    renderWithProviders(<InboxPage />);

    const table = await screen.findByRole("table");
    const summaryCell = within(table).getAllByText("Review mock decision")[0];
    await user.click(summaryCell);

    const undoButton = await screen.findByRole("button", { name: /Undo last action/i });
    await user.click(screen.getByRole("button", { name: "Snooze" }));

    await waitFor(() => {
      expect(within(table).getAllByText(/Snoozed/i).length).toBeGreaterThan(0);
    });

    await user.click(undoButton);
    await waitFor(() => {
      expect(within(table).getAllByText(/Open/).length).toBeGreaterThan(0);
    });
  });

  it("renders error state when the inbox endpoint fails", async () => {
    server.use(
      rest.get("http://localhost:3000/api/bff/inbox", (_req, res, ctx) =>
        res(ctx.status(500), ctx.json({ code: "ERROR", message: "Boom" }))
      )
    );

    renderWithProviders(<InboxPage />);
    await waitFor(() => expect(screen.getByText(/Unable to load inbox/i)).toBeInTheDocument());
  });
});
