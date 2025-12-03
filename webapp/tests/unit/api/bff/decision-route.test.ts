import { NextRequest } from "next/server";
import type { Session } from "next-auth";

import { GET, POST } from "@/app/api/bff/decision/route";
import { decisionApiClient } from "@/lib/api/decisionApiClient";
import type { DecisionRulesResponse } from "@/lib/api/decisionClient";
import type { SimulationScenario } from "@/lib/api/decisionTypes";
import { getServerAuthSession } from "@/lib/auth";
import type { components, paths } from "@/lib/api/types.generated";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

jest.mock("@/lib/api/decisionApiClient", () => ({
  decisionApiClient: {
    preview: jest.fn(),
    run: jest.fn(),
  },
}));

const mockGetSession = getServerAuthSession as jest.MockedFunction<typeof getServerAuthSession>;
const mockPreview = decisionApiClient.preview as jest.MockedFunction<typeof decisionApiClient.preview>;
const mockRun = decisionApiClient.run as jest.MockedFunction<typeof decisionApiClient.run>;

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Admin",
    email: "admin@example.com",
    roles,
  },
  expires: "",
});

const buildRequest = (path: string) => new NextRequest(new URL(`http://localhost${path}`));

describe("Decision BFF route", () => {
  afterEach(() => {
    mockGetSession.mockReset();
    mockPreview.mockReset();
    mockRun.mockReset();
  });

  it("returns rules for admin users", async () => {
    const previewResponse: paths["/decision/preview"]["get"]["responses"]["200"]["content"]["application/json"] = {
      planned: [
        {
          id: "task-1",
          source: "decision_engine",
          entity: { type: "sku_vendor", asin: "B001", vendor_id: 22 },
          decision: "request_price",
          priority: 80,
          status: "open",
          why: [{ code: "roi_low", message: "ROI low" }],
          alternatives: [{ action: "wait_until", label: "Wait" }],
          summary: "Test decision",
          created_at: "2024-01-01T00:00:00.000Z",
          updated_at: "2024-01-02T00:00:00.000Z",
          links: {},
        } as components["schemas"]["DecisionTask"],
      ],
      generated: 1,
      candidates: 1,
    };

    mockPreview.mockResolvedValue(previewResponse);
    mockGetSession.mockResolvedValue(buildSession(["admin"]));
    const response = await GET(buildRequest("/api/bff/decision?resource=rules"));
    expect(response.status).toBe(200);
    const payload = (await response.json()) as DecisionRulesResponse;
    expect(mockPreview).toHaveBeenCalledWith({ limit: 50 });
    expect(payload.rules.length).toBe(1);
    expect(payload.rules[0]).toMatchObject({ id: "request_price", isActive: true, actions: [{ action: "request_price" }] });
  });

  it("blocks non-admin users", async () => {
    mockGetSession.mockResolvedValue(buildSession(["ops"]));
    const response = await GET(buildRequest("/api/bff/decision?resource=rules"));
    expect(response.status).toBe(403);
  });

  it("builds a mock simulation response", async () => {
    const runResponse: paths["/decision/run"]["post"]["responses"]["200"]["content"]["application/json"] = {
      items: [
        {
          id: "task-2",
          source: "decision_engine",
          entity: { type: "sku_vendor", asin: "B002", vendor_id: 44 },
          decision: "request_discount",
          priority: 70,
          status: "open",
          why: [{ code: "roi_guardrail", message: "ROI below guardrail" }],
          alternatives: [{ action: "wait_until", label: "Observe" }],
          summary: "Request discount",
          created_at: "2024-01-03T00:00:00.000Z",
          updated_at: "2024-01-04T00:00:00.000Z",
          links: {},
        } as components["schemas"]["DecisionTask"],
      ],
      pagination: { page: 1, page_size: 1, total: 1, total_pages: 1 },
    };
    mockRun.mockResolvedValue(runResponse);
    mockGetSession.mockResolvedValue(buildSession(["admin"]));
    const request = new NextRequest(new URL("http://localhost/api/bff/decision"), {
      method: "POST",
      body: JSON.stringify({ ruleId: "rule-guardrail", input: { price: 10 } }),
    } as RequestInit);
    const response = await POST(request);
    expect(response.status).toBe(201);
    const scenario = (await response.json()) as SimulationScenario & { metrics?: SimulationScenario["result"] };
    expect(mockRun).toHaveBeenCalled();
    expect((scenario.decisions ?? []).length).toBeGreaterThan(0);
    expect((scenario.metrics ?? scenario.result)?.roi).toBeDefined();
  });
});
