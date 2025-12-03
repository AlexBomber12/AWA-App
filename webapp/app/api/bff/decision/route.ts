import { NextRequest, NextResponse } from "next/server";

import { errorResponse, handleApiError, requirePermission } from "@/app/api/bff/utils";
import type { DecisionSummary, Rule, SimulationScenario, Task } from "@/lib/api/bffTypes";
import type { DecisionPayload, SimulationInput } from "@/lib/api/decisionTypes";
import { decisionApiClient } from "@/lib/api/decisionApiClient";
import type { components, paths } from "@/lib/api/types.generated";
import { parsePositiveInt, parseString } from "@/lib/parsers";

import { toTask } from "../inbox/route";

type DecisionTask = components["schemas"]["DecisionTask"];
type DecisionPreviewResponse = paths["/decision/preview"]["get"]["responses"]["200"]["content"]["application/json"];
type DecisionRunResponse = paths["/decision/run"]["post"]["responses"]["200"]["content"]["application/json"];

export const dynamic = "force-dynamic";

const taskToRule = (task: Task): Rule => ({
  id: task.decision?.decision ?? task.id,
  name: task.summary ?? task.decision?.decision ?? task.id,
  description: task.decision?.defaultAction ?? task.summary ?? null,
  conditions: [],
  enabled: true,
  isActive: true,
  createdAt: task.createdAt,
  updatedAt: task.updatedAt,
  scope: "global",
  actions: task.decision ? [{ action: task.decision.decision as DecisionPayload["decision"] }] : [],
});

const toResultMetrics = (decision?: DecisionPayload) => {
  const metrics = decision?.metrics;
  if (!metrics) {
    return undefined;
  }
  return {
    roi: metrics.roi ?? 0,
    margin: metrics.maxCogs ?? metrics.revenueDelta ?? metrics.marginDelta ?? 0,
    riskAdjustedRoi: metrics.riskAdjustedRoi,
    maxCogs: metrics.maxCogs,
    revenueImpact: metrics.revenueDelta,
  };
};

const normalizeParameters = (value?: Record<string, unknown>): SimulationScenario["parameters"] => {
  if (!value) {
    return {};
  }
  const toParamValue = (input: unknown): string | number | boolean | null => {
    if (input === null) return null;
    if (typeof input === "string" || typeof input === "number" || typeof input === "boolean") {
      return input;
    }
    if (input === undefined) {
      return null;
    }
    return String(input);
  };
  return Object.fromEntries(Object.entries(value).map(([key, val]) => [key, toParamValue(val)]));
};

const taskToScenario = (task: Task, parameters: SimulationScenario["parameters"] = {}): SimulationScenario => {
  const decision = task.decision;
  const metrics = toResultMetrics(decision);
  const entity = task.entity as Record<string, unknown> | undefined;
  const asin = entity && typeof entity.asin === "string" ? entity.asin : undefined;
  const normalizedParams = normalizeParameters(parameters);
  const normalizedEntityParams = normalizeParameters(entity);

  return {
    id: task.id,
    name: task.summary ?? decision?.decision ?? task.id,
    description: decision?.defaultAction ?? task.description ?? undefined,
    ruleId: decision?.decision ?? task.type,
    baselineSku: asin ?? task.id,
    parameters: Object.keys(normalizedParams).length ? normalizedParams : normalizedEntityParams,
    result: metrics ?? { roi: 0, margin: 0 },
    metrics: metrics ?? undefined,
    decisions: decision ? [decision] : [],
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
  };
};

const buildSummary = (preview: DecisionPreviewResponse): DecisionSummary => {
  const tasks = (preview.planned ?? []).map((item) => toTask(item as DecisionTask));
  const rules = Array.from(
    tasks.reduce<Map<string, Rule>>((acc, task) => {
      const rule = taskToRule(task);
      if (!acc.has(rule.id)) {
        acc.set(rule.id, rule);
      }
      return acc;
    }, new Map()).values()
  );
  const scenarios = tasks.map((task) => taskToScenario(task));
  return { rules, scenarios, tasks };
};

export async function GET(request: NextRequest) {
  const permission = await requirePermission("decision", "view");
  if (!permission.ok) {
    return permission.response;
  }

  const resource = parseString(request.nextUrl.searchParams.get("resource"));
  const limit = parsePositiveInt(request.nextUrl.searchParams.get("limit"), 50);

  try {
    const preview = await decisionApiClient.preview({ limit });
    const summary = buildSummary(preview);

    if (resource === "rules") {
      return NextResponse.json({ data: summary.rules, rules: summary.rules });
    }
    if (resource === "scenarios") {
      return NextResponse.json({ data: summary.scenarios, scenarios: summary.scenarios });
    }

    return NextResponse.json({ data: summary, ...summary });
  } catch (error) {
    return handleApiError(error, "Unable to load decision previews.");
  }
}

const buildFallbackScenario = (payload: { ruleId?: string; input?: SimulationInput }): SimulationScenario => {
  const now = new Date().toISOString();
  return {
    id: payload.ruleId ?? `simulation-${Date.now()}`,
    name: payload.ruleId ? `Simulation for ${payload.ruleId}` : "Decision simulation",
    description: "Simulation created from user input.",
    ruleId: payload.ruleId ?? "simulation",
    baselineSku: (payload.input?.asin as string | undefined) ?? payload.ruleId ?? "simulation",
    parameters: (payload.input as SimulationScenario["parameters"]) ?? {},
    result: { roi: 0, margin: 0 },
    decisions: [],
    createdAt: now,
    updatedAt: now,
  };
};

export async function POST(request: NextRequest) {
  const permission = await requirePermission("decision", "configure");
  if (!permission.ok) {
    return permission.response;
  }

  let payload: { ruleId?: string; input?: SimulationInput };
  try {
    payload = (await request.json()) as { ruleId?: string; input?: SimulationInput };
  } catch {
    return errorResponse(400, "INVALID_REQUEST", "Malformed JSON payload.");
  }

  const limitValue = (payload.input as { limit?: number } | undefined)?.limit;
  const limit = parsePositiveInt(limitValue !== undefined ? String(limitValue) : undefined, 25);

  try {
    const response: DecisionRunResponse = await decisionApiClient.run({ limit });
    const tasks = (response.items ?? []).map((task) => toTask(task as DecisionTask));
    const updatedTask = tasks[0];
    const scenario = updatedTask
      ? taskToScenario(updatedTask, (payload.input as SimulationScenario["parameters"]) ?? {})
      : buildFallbackScenario(payload);
    return NextResponse.json({ data: scenario, ...scenario }, { status: 201 });
  } catch (error) {
    return handleApiError(error, "Unable to run decision simulation.");
  }
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
