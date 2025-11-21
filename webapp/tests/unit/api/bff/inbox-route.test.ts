import { NextRequest } from "next/server";
import type { Session } from "next-auth";

import { GET } from "@/app/api/bff/inbox/route";
import type { InboxListResponse } from "@/lib/api/inboxClient";
import { getServerAuthSession } from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

const mockGetSession = getServerAuthSession as jest.MockedFunction<typeof getServerAuthSession>;

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

  it("returns mock inbox tasks with pagination for ops users", async () => {
    mockGetSession.mockResolvedValue(buildSession(["ops"]));
    const response = await GET(buildRequest("state=open&page=1&pageSize=5"));
    expect(response.status).toBe(200);
    const payload = (await response.json()) as InboxListResponse;
    expect(payload.pagination).toEqual(expect.objectContaining({ page: 1, pageSize: 5 }));
    expect(payload.items.length).toBeGreaterThan(0);
    expect(payload.items[0]).toHaveProperty("decision.decision");
    expect(payload.items[0].alternatives?.[0]).toBeDefined();
  });
});
