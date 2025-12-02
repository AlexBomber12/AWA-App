import { NextRequest, NextResponse } from "next/server";

import { errorResponse, requirePermission } from "@/app/api/bff/utils";
import type { DecisionSummary, SimulationScenario } from "@/lib/api/bffTypes";
import type { SimulationInput } from "@/lib/api/decisionTypes";
import { parseString } from "@/lib/parsers";

import { DECISION_RULES, SIMULATION_SCENARIOS, buildSimulationScenario, findRuleById } from "./data";

const withIsActive = (rules: typeof DECISION_RULES) =>
  rules.map((rule) => ({
    ...rule,
    isActive: (rule as { isActive?: boolean }).isActive ?? Boolean(rule.enabled),
  }));

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const permission = await requirePermission("decision", "view");
  if (!permission.ok) {
    return permission.response;
  }

  const resource = parseString(request.nextUrl.searchParams.get("resource"));

  if (resource === "rules") {
    const rules = withIsActive(DECISION_RULES);
    return NextResponse.json({ data: rules, rules });
  }

  if (resource === "scenarios") {
    return NextResponse.json({ data: SIMULATION_SCENARIOS, scenarios: SIMULATION_SCENARIOS });
  }

  const payload: DecisionSummary = {
    rules: withIsActive(DECISION_RULES),
    scenarios: SIMULATION_SCENARIOS,
  };

  return NextResponse.json({ data: payload, ...payload });
}

export async function POST(request: NextRequest) {
  const permission = await requirePermission("decision", "configure");
  if (!permission.ok) {
    return permission.response;
  }

  let payload: { ruleId?: string; input?: Record<string, unknown> };
  try {
    payload = (await request.json()) as { ruleId?: string; input?: Record<string, unknown> };
  } catch (error) {
    console.error("Invalid simulation payload", error);
    return errorResponse(400, "INVALID_REQUEST", "Malformed JSON payload.");
  }

  if (!payload.ruleId) {
    return errorResponse(400, "INVALID_REQUEST", "Missing ruleId for simulation.");
  }

  const rule = findRuleById(payload.ruleId);
  if (!rule) {
    return errorResponse(404, "NOT_FOUND", "Rule not found for simulation.");
  }

  const scenario = buildSimulationScenario(rule.id, (payload.input ?? {}) as SimulationInput);
  const withMetrics: SimulationScenario & { metrics: SimulationScenario["result"] } = {
    ...scenario,
    metrics: scenario.result ?? scenario.metrics,
  };
  return NextResponse.json({ data: withMetrics, ...withMetrics }, { status: 201 });
}

const methodNotAllowed = () =>
  NextResponse.json(
    { error: { code: "METHOD_NOT_ALLOWED", message: "Only GET and POST are supported for this endpoint.", status: 405 } },
    {
      status: 405,
      headers: {
        Allow: "GET, POST",
      },
    }
  );

export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
export const DELETE = methodNotAllowed;
