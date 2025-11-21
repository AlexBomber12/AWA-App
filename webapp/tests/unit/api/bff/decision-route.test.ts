import { NextRequest } from "next/server";
import type { Session } from "next-auth";

import { GET, POST } from "@/app/api/bff/decision/route";
import type { DecisionRulesResponse } from "@/lib/api/decisionClient";
import type { SimulationScenario } from "@/lib/api/decisionTypes";
import { getServerAuthSession } from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

const mockGetSession = getServerAuthSession as jest.MockedFunction<typeof getServerAuthSession>;

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
  });

  it("returns rules for admin users", async () => {
    mockGetSession.mockResolvedValue(buildSession(["admin"]));
    const response = await GET(buildRequest("/api/bff/decision?resource=rules"));
    expect(response.status).toBe(200);
    const payload = (await response.json()) as DecisionRulesResponse;
    expect(payload.rules.length).toBeGreaterThan(0);
    expect(payload.rules[0]).toHaveProperty("isActive");
  });

  it("blocks non-admin users", async () => {
    mockGetSession.mockResolvedValue(buildSession(["ops"]));
    const response = await GET(buildRequest("/api/bff/decision?resource=rules"));
    expect(response.status).toBe(403);
  });

  it("builds a mock simulation response", async () => {
    mockGetSession.mockResolvedValue(buildSession(["admin"]));
    const request = new NextRequest(new URL("http://localhost/api/bff/decision"), {
      method: "POST",
      body: JSON.stringify({ ruleId: "rule-guardrail", input: { price: 10 } }),
    } as RequestInit);
    const response = await POST(request);
    expect(response.status).toBe(201);
    const scenario = (await response.json()) as SimulationScenario;
    expect(scenario.decisions.length).toBeGreaterThan(0);
    expect(scenario.metrics?.roi).toBeDefined();
  });
});
