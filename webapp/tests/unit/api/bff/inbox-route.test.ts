import { NextRequest } from "next/server";
import type { Session } from "next-auth";

import { GET } from "@/app/api/bff/inbox/route";
import type { InboxListResponse } from "@/lib/api/inboxClient";
import { getServerAuthSession } from "@/lib/auth";
import { inboxApiClient } from "@/lib/api/inboxApiClient";
import type { components } from "@/lib/api/types.generated";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

jest.mock("@/lib/api/inboxApiClient", () => ({
  inboxApiClient: {
    listTasks: jest.fn(),
  },
}));

const mockGetSession = getServerAuthSession as jest.MockedFunction<typeof getServerAuthSession>;
const mockListTasks = inboxApiClient.listTasks as jest.MockedFunction<typeof inboxApiClient.listTasks>;

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Test User",
    email: "test@example.com",
    roles,
  },
  expires: "",
});

const buildRequest = (query?: string) => {
  const url = new URL(`http://localhost/api/bff/inbox${query ? `?${query}` : ""}`);
  return new NextRequest(url);
};

describe("Inbox BFF route", () => {
  afterEach(() => {
    mockGetSession.mockReset();
    mockListTasks.mockReset();
  });

  it("rejects unauthenticated requests", async () => {
    mockGetSession.mockResolvedValueOnce(null);
    const response = await GET(buildRequest());
    expect(response.status).toBe(401);
  });

  it("rejects users without inbox permissions", async () => {
    mockGetSession.mockResolvedValue(buildSession(["viewer"]));
    const response = await GET(buildRequest());
    expect(response.status).toBe(403);
  });

  it("proxies inbox tasks with pagination for ops users", async () => {
    const backendTask: components["schemas"]["DecisionTask"] = {
      id: "task-1",
      source: "decision_engine",
      entity: { type: "sku_vendor", asin: "B00TEST", vendor_id: 22 },
      decision: "request_price",
      priority: 90,
      status: "open",
      why: [{ code: "roi_guardrail", message: "ROI low" }],
      alternatives: [{ action: "wait_until", label: "Wait" }],
      state: "open",
      summary: "Review ROI",
      created_at: "2024-01-01T00:00:00.000Z",
      updated_at: "2024-01-02T00:00:00.000Z",
      links: {},
    };

    mockListTasks.mockResolvedValue({
      items: [backendTask],
      pagination: { page: 1, page_size: 1, total: 1, total_pages: 1 },
      summary: { open: 1, in_progress: 0, blocked: 0, applied: 0, dismissed: 0, expired: 0, pending: 1, snoozed: 0 },
    });
    mockGetSession.mockResolvedValue(buildSession(["ops"]));
    const response = await GET(buildRequest("state=open&page=1&pageSize=5"));
    expect(response.status).toBe(200);
    const payload = (await response.json()) as InboxListResponse;
    expect(mockListTasks).toHaveBeenCalledWith(
      expect.objectContaining({ page: 1, pageSize: 5, state: "open", sort: "priority" })
    );
    expect(payload.pagination).toEqual(expect.objectContaining({ page: 1, pageSize: 1, total: 1 }));
    expect(payload.items[0]).toEqual(
      expect.objectContaining({
        id: "task-1",
        state: "open",
        decision: expect.objectContaining({ decision: "request_price" }),
        priority: "critical",
      })
    );
  });
});
