import { NextRequest, NextResponse } from "next/server";

import { buildPaginationMeta, handleApiError, parseSortMeta, requirePermission } from "@/app/api/bff/utils";
import type { Task, TaskPriority, TaskState } from "@/lib/api/bffTypes";
import type { DecisionMetrics, DecisionPayload, DecisionReason } from "@/lib/api/decisionTypes";
import { inboxApiClient } from "@/lib/api/inboxApiClient";
import type { components, paths } from "@/lib/api/types.generated";
import { parsePositiveInt, parseString } from "@/lib/parsers";

export const dynamic = "force-dynamic";

type InboxSort = "priority" | "deadline" | "createdAt";

type DecisionTask = components["schemas"]["DecisionTask"];
type DecisionReasonSchema = components["schemas"]["DecisionReason"];
type DecisionAlternativeSchema = components["schemas"]["DecisionAlternative"];
type DecisionTaskListResponse = paths["/inbox/tasks"]["get"]["responses"]["200"]["content"]["application/json"];

const PRIORITY_THRESHOLD: Record<TaskPriority, number> = {
  critical: 90,
  high: 70,
  medium: 40,
  low: 10,
};

const toTaskPriority = (priority: number | string | null | undefined): TaskPriority => {
  if (priority === "low" || priority === "medium" || priority === "high" || priority === "critical") {
    return priority;
  }
  const numeric = Number(priority);
  if (Number.isFinite(numeric)) {
    if (numeric >= PRIORITY_THRESHOLD.critical) return "critical";
    if (numeric >= PRIORITY_THRESHOLD.high) return "high";
    if (numeric >= PRIORITY_THRESHOLD.medium) return "medium";
    return "low";
  }
  return "medium";
};

const priorityFilterValue = (value?: string | null): number | undefined => {
  if (!value) {
    return undefined;
  }
  const numeric = Number(value);
  if (Number.isFinite(numeric)) {
    return numeric;
  }
  if (value in PRIORITY_THRESHOLD) {
    return PRIORITY_THRESHOLD[value as TaskPriority];
  }
  return undefined;
};

const normalizeState = (state: string | null | undefined): TaskState => {
  switch (state) {
    case "pending":
    case "open":
      return "open";
    case "applied":
    case "done":
      return "done";
    case "dismissed":
    case "cancelled":
      return "cancelled";
    case "expired":
    case "blocked":
      return "blocked";
    case "snoozed":
      return "snoozed";
    case "in_progress":
      return "in_progress";
    default:
      return "open";
  }
};

const toStatusFromState = (state: TaskState): Task["status"] => {
  switch (state) {
    case "done":
      return "completed";
    case "cancelled":
      return "archived";
    case "snoozed":
    case "blocked":
    case "in_progress":
      return "in_progress";
    default:
      return "open";
  }
};

const toDecisionReason = (reason: DecisionReasonSchema): DecisionReason => ({
  title: reason.message || reason.code,
  detail: typeof reason.data === "object" && reason.data !== null && "detail" in reason.data ? String(reason.data.detail) : undefined,
  code: reason.code,
  metric: reason.metric ?? undefined,
});

const normalizeMetrics = (metrics: DecisionTask["metrics"]): DecisionMetrics | undefined => {
  if (!metrics || typeof metrics !== "object") {
    return undefined;
  }

  const toNumber = (value: unknown): number | undefined => {
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : undefined;
  };

  return {
    roi: toNumber((metrics as Record<string, unknown>).roi),
    riskAdjustedRoi: toNumber((metrics as Record<string, unknown>).riskAdjustedRoi ?? (metrics as Record<string, unknown>).risk_adjusted_roi),
    maxCogs: toNumber((metrics as Record<string, unknown>).maxCogs ?? (metrics as Record<string, unknown>).max_cogs ?? (metrics as Record<string, unknown>).cogs),
    revenueDelta: toNumber((metrics as Record<string, unknown>).revenueDelta ?? (metrics as Record<string, unknown>).revenue_delta ?? (metrics as Record<string, unknown>).revenueImpact),
    marginDelta: toNumber((metrics as Record<string, unknown>).marginDelta ?? (metrics as Record<string, unknown>).margin_delta),
  };
};

const normalizeAlternatives = (alternatives: DecisionAlternativeSchema[] | undefined) =>
  (alternatives ?? []).map((alt) => ({
    decision: alt.action as DecisionPayload["decision"],
    label: alt.label ?? undefined,
    impact: alt.impact ?? undefined,
    why: (alt.why ?? []).map((reason) => toDecisionReason(reason)),
  }));

const toDecisionPayload = (task: DecisionTask): DecisionPayload => ({
  decision: task.decision as DecisionPayload["decision"],
  priority: task.priority,
  deadlineAt: task.deadline_at ?? undefined,
  defaultAction: task.default_action ?? undefined,
  why: (task.why ?? []).map((reason) => toDecisionReason(reason)),
  alternatives: normalizeAlternatives(task.alternatives),
  nextRequestAt: task.next_request_at ?? undefined,
  metrics: normalizeMetrics(task.metrics),
});

const normalizeEntity = (entity: DecisionTask["entity"]) => {
  if (!entity || typeof entity !== "object") {
    return undefined;
  }

  const type = (entity as { type?: string }).type;
  if (!type || typeof type !== "string") {
    return undefined;
  }

  const vendorId = (entity as { vendorId?: string | number; vendor_id?: string | number }).vendorId ?? (entity as { vendor_id?: string | number }).vendor_id;
  const asin = (entity as { asin?: string }).asin;
  const label = (entity as { label?: string }).label;
  const category = (entity as { category?: string }).category;

  if (type === "sku_vendor") {
    return {
      type: "sku_vendor" as const,
      asin: asin ?? "",
      vendorId: vendorId !== undefined && vendorId !== null ? String(vendorId) : "",
      label,
      category,
    };
  }

  if (type === "sku") {
    return {
      type: "sku" as const,
      asin: asin ?? "",
      sku: (entity as { sku?: string }).sku,
      vendorId: vendorId !== undefined && vendorId !== null ? String(vendorId) : undefined,
      label,
      category,
    };
  }

  if (type === "vendor") {
    return {
      type: "vendor" as const,
      vendorId: vendorId !== undefined && vendorId !== null ? String(vendorId) : "",
      id: (entity as { id?: string }).id,
      label,
    };
  }

  if (type === "thread") {
    return {
      type: "thread" as const,
      threadId: (entity as { threadId?: string; thread_id?: string }).threadId ?? (entity as { thread_id?: string }).thread_id ?? "",
      subject: (entity as { subject?: string }).subject,
      channel: (entity as { channel?: "email" | "slack" }).channel,
      label,
    };
  }

  if (type === "price_list") {
    return {
      type: "price_list" as const,
      id: (entity as { id?: string }).id ?? "",
      label,
      category,
    };
  }

  return undefined;
};

export const toTask = (task: DecisionTask): Task => {
  const decision = toDecisionPayload(task);
  const state = normalizeState(task.state);
  const entity = normalizeEntity(task.entity);

  return {
    id: task.id,
    type: entity?.type ?? task.source ?? "task",
    title: task.summary ?? decision.defaultAction ?? task.decision,
    description: decision.defaultAction ?? null,
    status: toStatusFromState(state),
    priority: toTaskPriority(task.priority),
    createdAt: task.created_at ?? new Date().toISOString(),
    updatedAt: task.updated_at ?? task.created_at ?? new Date().toISOString(),
    dueAt: task.deadline_at ?? null,
    deadlineAt: task.deadline_at ?? null,
    decisionId: task.decision,
    assignee: task.assignee ?? null,
    source: (task.source ?? null) as Task["source"],
    summary: task.summary ?? decision.defaultAction ?? task.decision,
    entity,
    decision,
    state,
    why: decision.why,
    alternatives: decision.alternatives,
    nextRequestAt: decision.nextRequestAt ?? null,
  };
};

const buildSummary = (summary?: DecisionTaskListResponse["summary"]) => {
  if (!summary) {
    return undefined;
  }
  return {
    open: summary.open ?? summary.pending ?? 0,
    inProgress: summary.in_progress ?? summary.snoozed ?? 0,
    blocked: summary.blocked ?? summary.expired ?? 0,
  };
};

const normalizeSort = (sort?: string | null): InboxSort => {
  if (sort === "deadline") {
    return "deadline";
  }
  if (sort === "createdAt" || sort === "created_at") {
    return "createdAt";
  }
  return "priority";
};

const mapSortForApi = (sort?: InboxSort) => {
  if (sort === "createdAt") {
    return "created_at";
  }
  return sort ?? "priority";
};

export async function GET(request: NextRequest) {
  const permission = await requirePermission("inbox", "view");
  if (!permission.ok) {
    return permission.response;
  }

  const params = request.nextUrl.searchParams;
  const page = parsePositiveInt(params.get("page"), 1);
  const pageSize = parsePositiveInt(params.get("pageSize") ?? params.get("limit"), 25);
  const state = parseString(params.get("state")) as TaskState | undefined;
  const source = parseString(params.get("source"));
  const assignee = parseString(params.get("assignee"));
  const search = parseString(params.get("search"));
  const taskId = parseString(params.get("taskId"));
  const priority = priorityFilterValue(parseString(params.get("priority")));
  const sort = normalizeSort(parseString(params.get("sort")) as InboxSort | undefined);

  try {
    const apiResponse = await inboxApiClient.listTasks({
      page,
      pageSize,
      state,
      source,
      assignee,
      search,
      taskId,
      priority,
      sort: mapSortForApi(sort),
    });

    const items = (apiResponse.items ?? []).map((task) => toTask(task));
    const pagination = apiResponse.pagination ?? { page, page_size: pageSize, total: items.length, total_pages: 1 };
    const total = pagination.total ?? items.length;

    return NextResponse.json({
      data: items,
      items,
      pagination: buildPaginationMeta(pagination.page ?? page, pagination.page_size ?? pageSize, total),
      sort: parseSortMeta(sort),
      filters: { state, source, assignee, priority, search, taskId },
      summary: buildSummary(apiResponse.summary),
    });
  } catch (error) {
    return handleApiError(error, "Unable to load inbox tasks.");
  }
}

const methodNotAllowed = () =>
  NextResponse.json(
    { error: { code: "METHOD_NOT_ALLOWED", message: "Only GET is supported for this endpoint.", status: 405 } },
    {
      status: 405,
      headers: {
        Allow: "GET",
      },
    }
  );

export const POST = methodNotAllowed;
export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
export const DELETE = methodNotAllowed;
