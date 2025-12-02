import type { DecisionPayload, SimulationInput } from "@/lib/api/decisionTypes";
import type { Rule, SimulationResult, SimulationScenario } from "@/lib/api/bffTypes";

const BASE_DATE = Date.parse("2024-04-15T12:00:00.000Z");

const buildDecision = (decision: DecisionPayload): DecisionPayload => ({
  ...decision,
  why: [...decision.why],
  alternatives: [...decision.alternatives],
});

const toResult = (metrics: SimulationResult): SimulationResult => {
  const roi = metrics.roi ?? 0;
  const maxCogs = metrics.maxCogs ?? 0;
  const margin = Number((metrics.revenueImpact ?? maxCogs).toFixed(2));
  const breakEvenPrice = maxCogs ? Number((maxCogs * 1.05).toFixed(2)) : undefined;

  return {
    roi,
    margin,
    riskAdjustedRoi: metrics.riskAdjustedRoi,
    maxCogs,
    revenueImpact: metrics.revenueImpact,
    breakEvenPrice,
  };
};

export const DECISION_RULES: Rule[] = [
  {
    id: "rule-guardrail",
    name: "ROI Guardrail Enforcement",
    description: "Flags SKU and vendor pairs when ROI drops below 15% and proposes a discount request.",
    scope: "category",
    conditions: [
      { category: "Home", field: "roi", op: "<", value: 15, cadenceDays: 7 },
      {
        expression: "volatility_pct > 5",
        value: "rolling_volatility",
        op: ">",
        cadenceDays: 3,
      },
    ],
    actions: [
      { action: "request_discount", defaultAction: "Email vendor for 5% discount", undoWindowHours: 6 },
      { action: "wait_until", cadenceDays: 1, defaultAction: "Observe for 24h" },
    ],
    cadence: { type: "rolling", days: 7 },
    enabled: true,
    createdAt: new Date(BASE_DATE - 30 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 5 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "rule-vendor-late",
    name: "Vendor Lead Time Drift",
    description: "Detects vendor shipments exceeding planned lead time by > 2 days and blocks repricing.",
    scope: "vendor",
    conditions: [
      { field: "lead_time_slip", op: ">", value: 2, vendorId: "2042" },
      { field: "on_time_rate", op: "<", value: 0.8, vendorId: "2042" },
    ],
    actions: [{ action: "blocked_observe", defaultAction: "Pause repricing until inbound clears" }],
    cadence: { type: "calendar", days: 14 },
    enabled: false,
    createdAt: new Date(BASE_DATE - 24 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 12 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "rule-category-promo",
    name: "Category Promo Simulation",
    description: "Projects ROI impact for promo campaigns in Home and Outdoors categories.",
    scope: "campaign",
    conditions: [
      { category: "Home", op: "in", value: ["Home", "Outdoors"] },
      { field: "promo_flag", op: "==", value: true, cadenceDays: 14 },
    ],
    actions: [
      { action: "update_price", defaultAction: "Apply +1.5% guardrail adjustment" },
      { action: "wait_until", defaultAction: "Observe promo performance for 24h" },
    ],
    cadence: { type: "calendar", days: 14 },
    enabled: true,
    createdAt: new Date(BASE_DATE - 40 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 8 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "rule-global-harm",
    name: "Global Price Harmonization",
    description: "Ensures price deltas stay within tolerance across NA/EU regions.",
    scope: "global",
    conditions: [{ field: "geo_price_delta", op: ">", value: 7.5, expression: "delta_pct" }],
    actions: [
      { action: "update_price", defaultAction: "Raise NA price by 1%" },
      { action: "continue", defaultAction: "Leave EU prices unchanged" },
    ],
    cadence: { type: "rolling", days: 10 },
    enabled: true,
    createdAt: new Date(BASE_DATE - 60 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 6 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export const SIMULATION_SCENARIOS: SimulationScenario[] = [
  {
    id: "scenario-guardrail-1",
    name: "Home ROI boost",
    description: "Applies ROI guardrail rule to the Home category promo batch.",
    ruleId: "rule-guardrail",
    baselineSku: "rule-guardrail",
    parameters: {
      price: 24.5,
      cost: 13.2,
      volatility: 5.5,
      category: "Home",
      observeOnly: false,
    },
    result: toResult({
      roi: 18.6,
      riskAdjustedRoi: 16.2,
      maxCogs: 14.8,
      revenueImpact: 4200,
      margin: 14.8,
    }),
    decisions: [
      buildDecision({
        decision: "update_price",
        priority: "high",
        deadlineAt: new Date(BASE_DATE + 24 * 60 * 60 * 1000).toISOString(),
        defaultAction: "Apply +1.5% price increase",
        why: ["ROI under guardrail in last 48h", "Promo discount expiring"],
        alternatives: [
          { decision: "request_discount", label: "Request vendor support" },
          { decision: "wait_until", label: "Re-run simulation tomorrow" },
        ],
      }),
      buildDecision({
        decision: "request_price",
        priority: "medium",
        defaultAction: "Send updated quote request to vendor",
        why: ["Last quote expired", "Freight cost increased 5%"],
        alternatives: [
          { decision: "switch_vendor", label: "Switch vendor for promo duration" },
          { decision: "continue", label: "Keep current price" },
        ],
        nextRequestAt: new Date(BASE_DATE + 72 * 60 * 60 * 1000).toISOString(),
      }),
    ],
    createdAt: new Date(BASE_DATE - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "scenario-vendor-2",
    name: "Vendor backlog follow-up",
    description: "Tests vendor backlog rule with increased lead-time tolerance.",
    ruleId: "rule-vendor-late",
    baselineSku: "rule-vendor-late",
    parameters: {
      volatility: 3.2,
      observeOnly: true,
    },
    result: toResult({
      roi: 16.4,
      riskAdjustedRoi: 12.2,
      maxCogs: 11.1,
      margin: 11.1,
    }),
    decisions: [
      buildDecision({
        decision: "blocked_observe",
        priority: "medium",
        defaultAction: "Pause repricing until inbound clears",
        why: ["Lead time variance exceeds tolerance", "On-time rate below 80%"],
        alternatives: [{ decision: "wait_until", label: "Re-evaluate after receiving inbound" }],
      }),
    ],
    createdAt: new Date(BASE_DATE - 7 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "scenario-harmonize-3",
    name: "Global harmonization dry run",
    description: "Ensures global price harmonization rule can be simulated.",
    ruleId: "rule-global-harm",
    baselineSku: "rule-global-harm",
    parameters: {
      category: "Electronics",
      price: 32.4,
      cost: 14.8,
    },
    result: toResult({
      roi: 21.5,
      riskAdjustedRoi: 18.5,
      maxCogs: 18.4,
      revenueImpact: 1800,
      margin: 18.4,
    }),
    decisions: [
      buildDecision({
        decision: "update_price",
        priority: "medium",
        defaultAction: "Raise NA price by 1%",
        why: ["Price delta between NA/EU exceeds 7.5%"],
        alternatives: [{ decision: "continue", label: "Leave pricing as-is" }],
      }),
    ],
    createdAt: new Date(BASE_DATE - 14 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

export const findRuleById = (ruleId: string) => DECISION_RULES.find((rule) => rule.id === ruleId);

const serializeInput = (input: SimulationInput) => JSON.stringify(input ?? {}, Object.keys(input ?? {}).sort());

export const buildSimulationScenario = (ruleId: string, input: SimulationInput): SimulationScenario => {
  const rule = findRuleById(ruleId);
  const reference = serializeInput(input ?? {});
  const score = reference.length + ruleId.length;
  const roi = Math.min(24, 12 + score * 0.2);
  const riskAdjustedRoi = roi - 3;
  const maxCogs = Number((15 + score * 0.05).toFixed(2));
  const revenueImpact = 420 + score;

  const parameters = Object.fromEntries(
    Object.entries(input ?? {}).map(([key, value]) => [
      key,
      typeof value === "string" || typeof value === "number" || typeof value === "boolean" ? value : String(value ?? ""),
    ])
  );

  const baselineSku = typeof parameters.asin === "string" ? parameters.asin : ruleId;
  const result: SimulationResult = {
    roi,
    margin: Number((maxCogs || roi).toFixed(2)),
    riskAdjustedRoi,
    maxCogs,
    revenueImpact,
    breakEvenPrice: Number((maxCogs * 1.05).toFixed(2)),
  };

  const decisionBase: DecisionPayload = {
    decision: "update_price",
    priority: "high",
    defaultAction: "Apply immediate 1% price increase",
    why: ["Simulated uplift requires price change"],
    alternatives: [
      { decision: "request_discount", label: "Request 3% vendor concession" },
      { decision: "wait_until", label: "Wait until ROI stabilizes" },
    ],
    metrics: { roi, riskAdjustedRoi, maxCogs },
  };

  return {
    id: `scenario-${ruleId}-${score}`,
    name: `${rule?.name ?? "Decision"} simulation`,
    description: `Mock result for ${rule?.name ?? "selection"} using ${Object.keys(input ?? {}).length} inputs.`,
    ruleId,
    baselineSku,
    parameters,
    result,
    decisions: [
      buildDecision(decisionBase),
      buildDecision({
        decision: "wait_until",
        priority: "medium",
        defaultAction: "Hold until next ingest cycle",
        why: ["Need follow-up simulation with vendor data"],
        alternatives: [{ decision: "continue", label: "Keep current pricing" }],
        nextRequestAt: new Date(BASE_DATE + 24 * 60 * 60 * 1000).toISOString(),
        metrics: { roi: roi - 1, riskAdjustedRoi: riskAdjustedRoi - 1, maxCogs },
      }),
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
};
