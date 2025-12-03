import { fetchDecisionSummary, runSimulation } from "@/lib/api/decisionClient";
import { fetchFromBff } from "@/lib/api/fetchFromBff";

jest.mock("@/lib/api/fetchFromBff", () => ({
  fetchFromBff: jest.fn(),
}));

const mockFetch = fetchFromBff as jest.MockedFunction<typeof fetchFromBff>;

describe("decisionClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("fetches decision summary from the BFF", async () => {
    mockFetch.mockResolvedValue({
      data: {
        rules: [{ id: "rule-1", name: "Rule One", description: null, conditions: [], actions: [], enabled: true, isActive: true, createdAt: "", updatedAt: "" }],
        scenarios: [],
      },
    });

    const summary = await fetchDecisionSummary();
    expect(mockFetch).toHaveBeenCalledWith("/api/bff/decision", expect.objectContaining({ method: "GET" }));
    expect(summary.rules[0]?.id).toBe("rule-1");
  });

  it("posts simulation payload to the BFF", async () => {
    mockFetch.mockResolvedValue({ data: { id: "scenario-1" } });

    await runSimulation({ ruleId: "rule-1", input: { price: 12 } });

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/bff/decision",
      expect.objectContaining({
        method: "POST",
        body: expect.any(String),
      })
    );
    const parsed = JSON.parse((mockFetch.mock.calls[0]?.[1]?.body as string) ?? "{}");
    expect(parsed.ruleId).toBe("rule-1");
  });
});
