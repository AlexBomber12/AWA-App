import type { Rule, SimulationScenario } from "@/lib/api/decisionClient";

const now = Date.now();

export const DECISION_RULES: Rule[] = [
  {
    id: "rule-1",
    name: "ROI Guardrail Enforcement",
    description: "Flags SKUs with ROI below 18% for operator review.",
    active: true,
    scope: "sku",
    params: {
      roiMin: 18,
      rollingWindowDays: 7,
    },
    createdAt: new Date(now - 10 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "rule-2",
    name: "Vendor Lead Time Drift",
    description: "Detect vendor shipments that exceed planned lead times by > 2 days.",
    active: false,
    scope: "vendor",
    params: {
      leadTimeToleranceDays: 2,
      alertThreshold: 0.2,
    },
    createdAt: new Date(now - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "rule-3",
    name: "Category Promo Simulation",
    description: "Projects ROI impact when promotional pricing is applied to top SKUs.",
    active: true,
    scope: "category",
    params: {
      categories: ["Home", "Outdoors"],
      cadenceDays: 14,
    },
    createdAt: new Date(now - 45 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(now - 5 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "rule-4",
    name: "Global Price Harmonization",
    description: "Ensures price deltas stay within tolerance across geographies.",
    active: true,
    scope: "global",
    params: {
      maxDeltaPercent: 7.5,
      includeVendors: ["Northwind Foods", "Evergreen Brands"],
    },
    createdAt: new Date(now - 60 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export const SIMULATION_SCENARIOS: SimulationScenario[] = [
  {
    id: "scenario-1",
    name: "Home ROI boost",
    description: "Applies ROI guardrail rule to the Home category promotion batch.",
    ruleId: "rule-3",
    input: {
      roiDelta: 4.5,
      priceChangePct: 2,
    },
    result: {
      summary: "Projected +3.1% blended ROI for 146 SKUs with minimal vendor risk.",
      stats: {
        affectedSkus: 146,
        avgRoiDelta: 3.1,
        blockedVendors: 2,
      },
      sampleDecisions: [
        {
          decision: "update_price",
          priority: "high",
          deadlineAt: new Date(now + 24 * 60 * 60 * 1000).toISOString(),
          defaultAction: "Apply +1.5% price increase",
          why: ["ROI under guardrail in last 48h", "Promo discount expiring"],
          alternatives: ["Request discount", "Wait until next promo window"],
        },
        {
          decision: "request_price",
          priority: "medium",
          defaultAction: "Send updated quote request to vendor",
          why: ["Last quote expired", "Freight cost increased 5%"],
          alternatives: ["Switch vendor", "Snooze until inbound shipment"],
          nextRequestAt: new Date(now + 72 * 60 * 60 * 1000).toISOString(),
        },
      ],
    },
  },
  {
    id: "scenario-2",
    name: "Vendor backlog follow-up",
    description: "Tests vendor backlog rule with increased lead-time tolerance.",
    ruleId: "rule-2",
    input: {
      leadTimeToleranceDays: 4,
    },
  },
  {
    id: "scenario-3",
    name: "Global harmonization dry run",
    description: "Ensures the global price harmonization rule can be simulated.",
    ruleId: "rule-4",
    input: {
      region: "NA/EU",
      tolerance: 5.5,
    },
  },
];

export const findRuleById = (ruleId: string) => DECISION_RULES.find((rule) => rule.id === ruleId);

const serializeInput = (input: Record<string, unknown>) => JSON.stringify(input, Object.keys(input).sort());

export const buildSimulationScenario = (ruleId: string, input: Record<string, unknown>): SimulationScenario => {
  const rule = findRuleById(ruleId);
  const reference = serializeInput(input ?? {});
  const score = reference.length + ruleId.length;
  const affectedSkus = 40 + score * 2;
  const roiDelta = Number((Math.min(5 + score * 0.1, 15)).toFixed(2));

  return {
    id: `scenario-${ruleId}-${score}`,
    name: `${rule?.name ?? "Decision"} simulation`,
    description: `Mock result for ${rule?.name ?? "selection"} using ${Object.keys(input ?? {}).length} inputs.`,
    ruleId,
    input,
    result: {
      summary: `Projected ROI delta of ${roiDelta}% across ${affectedSkus} SKUs.`,
      stats: {
        affectedSkus,
        avgRoiDelta: roiDelta,
        projectedRevenue: affectedSkus * 420,
      },
      sampleDecisions: [
        {
          decision: "update_price",
          priority: "high",
          defaultAction: "Apply immediate 1% price increase",
          why: ["Simulated uplift requires price change"],
          alternatives: ["Request discount", "Wait until ROI stabilizes"],
        },
        {
          decision: "wait_until",
          priority: "medium",
          defaultAction: "Hold until next ingest cycle",
          why: ["Need follow-up simulation with vendor data"],
          alternatives: ["Continue", "Switch vendor"],
          nextRequestAt: new Date(now + 24 * 60 * 60 * 1000).toISOString(),
        },
      ],
    },
  };
};
