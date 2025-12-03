import { NextRequest } from "next/server";
import type { Session } from "next-auth";

import { POST as applyHandler } from "@/app/api/bff/inbox/tasks/[taskId]/apply/route";
import { POST as snoozeHandler } from "@/app/api/bff/inbox/tasks/[taskId]/snooze/route";
import { getServerAuthSession } from "@/lib/auth";
import { inboxApiClient } from "@/lib/api/inboxApiClient";
import type { components } from "@/lib/api/types.generated";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

jest.mock("@/lib/api/inboxApiClient", () => ({
  inboxApiClient: {
    applyTask: jest.fn(),
    snoozeTask: jest.fn(),
  },
}));

const mockGetSession = getServerAuthSession as jest.MockedFunction<typeof getServerAuthSession>;
const mockApplyTask = inboxApiClient.applyTask as jest.MockedFunction<typeof inboxApiClient.applyTask>;
const mockSnoozeTask = inboxApiClient.snoozeTask as jest.MockedFunction<typeof inboxApiClient.snoozeTask>;

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Ops",
    email: "ops@example.com",
    roles,
  },
  expires: "",
});

const backendTask: components["schemas"]["DecisionTask"] = {
  id: "task-1",
  source: "decision_engine",
  entity: { type: "sku_vendor", asin: "B00TEST", vendor_id: 22 },
  decision: "request_price",
  priority: 80,
  status: "open",
  why: [{ code: "roi", message: "ROI low" }],
  alternatives: [],
  state: "open",
  summary: "Review ROI",
  created_at: "2024-01-01T00:00:00.000Z",
  updated_at: "2024-01-02T00:00:00.000Z",
  links: {},
};

describe("Inbox BFF task actions", () => {
  afterEach(() => {
    mockGetSession.mockReset();
    mockApplyTask.mockReset();
    mockSnoozeTask.mockReset();
  });

  it("proxies apply action to backend", async () => {
    mockGetSession.mockResolvedValue(buildSession(["ops"]));
    mockApplyTask.mockResolvedValue(backendTask);

    const request = new NextRequest(new URL("http://localhost/api/bff/inbox/tasks/task-1/apply"), { method: "POST" } as RequestInit);
    const response = await applyHandler(request, { params: { taskId: "task-1" } });

    expect(response.status).toBe(200);
    expect(mockApplyTask).toHaveBeenCalledWith("task-1", null);
    const payload = (await response.json()) as { data: { id: string; decision: { decision: string }; priority: string } };
    expect(payload.data.id).toBe("task-1");
    expect(payload.data.decision.decision).toBe("request_price");
  });

  it("forwards snooze payload to backend", async () => {
    mockGetSession.mockResolvedValue(buildSession(["ops"]));
    mockSnoozeTask.mockResolvedValue({ ...backendTask, state: "snoozed", next_request_at: "2024-01-05T00:00:00.000Z" });

    const request = new NextRequest(new URL("http://localhost/api/bff/inbox/tasks/task-1/snooze"), {
      method: "POST",
      body: JSON.stringify({ next_request_at: "2024-01-05T00:00:00.000Z" }),
    } as RequestInit);
    const response = await snoozeHandler(request, { params: { taskId: "task-1" } });

    expect(response.status).toBe(200);
    expect(mockSnoozeTask).toHaveBeenCalledWith("task-1", { next_request_at: "2024-01-05T00:00:00.000Z" });
    const payload = (await response.json()) as { data: { state?: string } };
    expect(payload.data.state).toBe("snoozed");
  });
});
