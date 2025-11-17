import { NextRequest, NextResponse } from "next/server";

import type { DecisionRulesResponse, SimulationScenariosResponse } from "@/lib/api/decisionClient";

import { DECISION_RULES, SIMULATION_SCENARIOS } from "./data";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const resource = request.nextUrl.searchParams.get("resource");

  if (resource === "rules") {
    const payload: DecisionRulesResponse = {
      rules: DECISION_RULES,
    };
    return NextResponse.json(payload);
  }

  if (resource === "scenarios") {
    const payload: SimulationScenariosResponse = {
      scenarios: SIMULATION_SCENARIOS,
    };
    return NextResponse.json(payload);
  }

  const payload: DecisionRulesResponse & SimulationScenariosResponse = {
    rules: DECISION_RULES,
    scenarios: SIMULATION_SCENARIOS,
  };

  return NextResponse.json(payload);
}
