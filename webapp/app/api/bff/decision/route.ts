import { NextRequest, NextResponse } from "next/server";

import type { DecisionRulesResponse, SimulationScenariosResponse } from "@/lib/api/decisionClient";
import type { SimulationScenario } from "@/lib/api/decisionTypes";
import { getServerAuthSession } from "@/lib/auth";
import { parseString } from "@/lib/parsers";
import { can, getUserRolesFromSession } from "@/lib/permissions/server";

import { DECISION_RULES, SIMULATION_SCENARIOS, buildSimulationScenario, findRuleById } from "./data";

export const dynamic = "force-dynamic";

const errorResponse = (status: number, code: string, message: string) =>
  NextResponse.json({ code, message, status }, { status });

export async function GET(request: NextRequest) {
  const session = await getServerAuthSession();
  if (!session) {
    return errorResponse(401, "UNAUTHORIZED", "Authentication required.");
  }

  const roles = getUserRolesFromSession(session);
  if (!can({ resource: "decision", action: "view", roles })) {
    return errorResponse(403, "FORBIDDEN", "You do not have access to Decision Engine data.");
  }

  const resource = parseString(request.nextUrl.searchParams.get("resource"));

  if (resource === "rules") {
    const payload: DecisionRulesResponse = { rules: DECISION_RULES };
    return NextResponse.json(payload);
  }

  if (resource === "scenarios") {
    const payload: SimulationScenariosResponse = { scenarios: SIMULATION_SCENARIOS };
    return NextResponse.json(payload);
  }

  const payload: DecisionRulesResponse & SimulationScenariosResponse = {
    rules: DECISION_RULES,
    scenarios: SIMULATION_SCENARIOS,
  };

  return NextResponse.json(payload);
}

export async function POST(request: NextRequest) {
  const session = await getServerAuthSession();
  if (!session) {
    return errorResponse(401, "UNAUTHORIZED", "Authentication required.");
  }

  const roles = getUserRolesFromSession(session);
  if (!can({ resource: "decision", action: "configure", roles })) {
    return errorResponse(403, "FORBIDDEN", "You do not have access to run simulations.");
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

  const scenario: SimulationScenario = buildSimulationScenario(rule.id, (payload.input ?? {}) as SimulationScenario["input"]);
  return NextResponse.json(scenario, { status: 201 });
}

const methodNotAllowed = () =>
  NextResponse.json(
    { code: "METHOD_NOT_ALLOWED", message: "Only GET and POST are supported for this endpoint.", status: 405 },
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
