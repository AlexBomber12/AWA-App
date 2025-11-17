import { NextRequest, NextResponse } from "next/server";

import type { RunSimulationPayload } from "@/lib/api/decisionClient";

import { buildSimulationScenario, findRuleById } from "../data";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const payload = (await request.json()) as RunSimulationPayload | null;
    if (!payload?.ruleId) {
      return NextResponse.json(
        { code: "INVALID_PAYLOAD", message: "ruleId is required.", status: 400 },
        { status: 400 }
      );
    }

    const rule = findRuleById(payload.ruleId);
    if (!rule) {
      return NextResponse.json(
        { code: "RULE_NOT_FOUND", message: `Rule ${payload.ruleId} not found.`, status: 404 },
        { status: 404 }
      );
    }

    const scenario = buildSimulationScenario(payload.ruleId, payload.input ?? {});
    return NextResponse.json(scenario);
  } catch (error) {
    console.error("Decision simulation mock failed", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to run simulation.", status: 500 },
      { status: 500 }
    );
  }
}
