import { NextRequest, NextResponse } from "next/server";

import { buildPaginationMeta, requirePermission } from "@/app/api/bff/utils";
import type { Task, TaskPriority, TaskState } from "@/lib/api/bffTypes";
import type { DecisionPriority } from "@/lib/api/decisionTypes";
import { parsePositiveInt, parseString } from "@/lib/parsers";

export const dynamic = "force-dynamic";

type InboxSort = "priority" | "deadline" | "createdAt";

const BASE_DATE = Date.parse("2024-04-15T12:00:00.000Z");

const toTaskPriority = (priority: DecisionPriority | undefined): TaskPriority => {
  if (priority === "low" || priority === "medium" || priority === "high" || priority === "critical") {
    return priority;
  }
  if (typeof priority === "number") {
    if (priority >= 90) return "critical";
    if (priority >= 70) return "high";
    if (priority >= 40) return "medium";
    return "low";
  }
  return "medium";
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

type InboxTaskInput = {
  id: string;
  source: Task["source"];
  entity: Task["entity"];
  summary: string;
  assignee?: string;
  state: TaskState;
  decision: NonNullable<Task["decision"]>;
  createdAt: string;
  updatedAt: string;
};

const buildTask = (task: InboxTaskInput): Task => {
  const priority = toTaskPriority(task.decision.priority);
  const deadline = task.decision.deadlineAt ?? null;

  return {
    id: task.id,
    type: task.entity?.type ?? task.source ?? "task",
    title: task.summary,
    description: task.decision.defaultAction ?? null,
    status: toStatusFromState(task.state),
    priority,
    createdAt: task.createdAt,
    updatedAt: task.updatedAt,
    dueAt: deadline,
    decisionId: task.decision.decision,
    assignee: task.assignee ?? null,
    source: task.source ?? null,
    summary: task.summary,
    entity: task.entity,
    decision: task.decision,
    state: task.state,
    why: task.decision.why,
    alternatives: task.decision.alternatives,
    nextRequestAt: task.decision.nextRequestAt ?? null,
  };
};

const MOCK_TASKS: Task[] = [
  buildTask({
    id: "task-roi-001",
    source: "decision_engine",
    entity: {
      type: "sku_vendor",
      asin: "B00VB001",
      vendorId: "2042",
      label: "FlexSmart Yoga Mat · Vendor 2042",
      category: "Sports",
    },
    summary: "Request discount to restore ROI guardrail",
    assignee: "Tara Nguyen",
    state: "open",
    decision: {
      decision: "request_discount",
      priority: 92,
      deadlineAt: new Date(BASE_DATE + 36 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Ask vendor for 5% discount and refreshed quote",
      why: [
        { title: "ROI below guardrail", detail: "11.5% vs 15% target", code: "roi_guardrail" },
        { title: "Freight up 6%", detail: "Lane cost change in last ingest" },
      ],
      alternatives: [
        { decision: "switch_vendor", label: "Switch to backup vendor (ROI +3.4%)" },
        { decision: "wait_until", label: "Observe 24h before repricing", impact: "Keep buy box stability" },
      ],
      nextRequestAt: new Date(BASE_DATE + 72 * 60 * 60 * 1000).toISOString(),
      metrics: { roi: 11.5, riskAdjustedRoi: 9.2, maxCogs: 13.4 },
    },
    createdAt: new Date(BASE_DATE - 4 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 60 * 60 * 1000).toISOString(),
  }),
  buildTask({
    id: "task-email-002",
    source: "email",
    entity: {
      type: "thread",
      threadId: "INBOX-204",
      subject: "Vendor follow-up for onboarding",
      label: "Northwind Foods thread",
    },
    summary: "Complete vendor onboarding documents",
    assignee: "Jordan Miles",
    state: "in_progress",
    decision: {
      decision: "continue",
      priority: "medium",
      defaultAction: "Finish onboarding checklist and attach W-9",
      why: [
        { title: "Pending paperwork", detail: "W-9 missing signature" },
        "Vendor asked for onboarding guidance in last email",
      ],
      alternatives: [{ decision: "wait_until", label: "Hold until vendor response" }],
    },
    createdAt: new Date(BASE_DATE - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 4 * 60 * 60 * 1000).toISOString(),
  }),
  buildTask({
    id: "task-uom-003",
    source: "system",
    entity: {
      type: "price_list",
      id: "PL-902",
      label: "Outdoor Spring Promo",
      category: "Outdoors",
    },
    summary: "Review UoM discrepancy in promo price list",
    assignee: "Ops Queue",
    state: "blocked",
    decision: {
      decision: "review_uom",
      priority: "high",
      deadlineAt: new Date(BASE_DATE + 5 * 24 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Confirm unit conversion with vendor before applying price",
      why: [
        { title: "Carton vs unit mismatch", detail: "12-pack carton treated as each" },
        { title: "Simulation risk", detail: "Virtual buyer flagged >6% ROI swing" },
      ],
      alternatives: [
        { decision: "wait_until", label: "Lock until clarity", impact: "Avoid ROI dip" },
        { decision: "request_price", label: "Request corrected price list" },
      ],
      metrics: { roi: 18.2, riskAdjustedRoi: 15.1, maxCogs: 21.4 },
    },
    createdAt: new Date(BASE_DATE - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 12 * 60 * 60 * 1000).toISOString(),
  }),
  buildTask({
    id: "task-alt-004",
    source: "decision_engine",
    entity: {
      type: "sku",
      asin: "B00ALT004",
      label: "Nimbus Smart Air Purifier",
      category: "Home",
    },
    summary: "Approve ROI guardrail exception",
    assignee: "Priya Patel",
    state: "snoozed",
    decision: {
      decision: "blocked_observe",
      priority: "high",
      deadlineAt: new Date(BASE_DATE + 10 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Pause price change until volatility cools",
      why: [
        { title: "High volatility", detail: "ROI fluctuated ±8% in last 24h" },
        "Virtual buyer flagged risk-adjusted ROI below 12%",
      ],
      alternatives: [
        { decision: "continue", label: "Keep prices steady" },
        { decision: "wait_until", label: "Re-evaluate after next ingest", impact: "Lower risk" },
      ],
      nextRequestAt: new Date(BASE_DATE + 18 * 60 * 60 * 1000).toISOString(),
      metrics: { roi: 19.4, riskAdjustedRoi: 12.1 },
    },
    createdAt: new Date(BASE_DATE - 10 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 30 * 60 * 1000).toISOString(),
  }),
  buildTask({
    id: "task-done-005",
    source: "decision_engine",
    entity: {
      type: "vendor",
      vendorId: "301",
      label: "Evergreen Brands",
    },
    summary: "Switch vendor for low-performing SKU bundle",
    assignee: "Automation",
    state: "done",
    decision: {
      decision: "switch_vendor",
      priority: "medium",
      why: [
        { title: "Better landed cost", detail: "Backup vendor offers -4% cost" },
        "Primary vendor PO delayed 9 days",
      ],
      alternatives: [
        { decision: "request_discount", label: "Negotiate with primary vendor" },
        { decision: "wait_until", label: "Wait until inbound shipment clears" },
      ],
    },
    createdAt: new Date(BASE_DATE - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(BASE_DATE - 2 * 24 * 60 * 60 * 1000).toISOString(),
  }),
];

const errorResponse = (status: number, code: string, message: string) =>
  NextResponse.json({ error: { code, message, status } }, { status });

const normalizePriority = (value?: string | null): TaskPriority | undefined => {
  if (!value) {
    return undefined;
  }
  if (value === "low" || value === "medium" || value === "high" || value === "critical") {
    return value;
  }
  const numeric = Number(value);
  if (Number.isFinite(numeric)) {
    return toTaskPriority(numeric);
  }
  return undefined;
};

const priorityWeight = (priority?: TaskPriority): number => {
  switch (priority) {
    case "critical":
      return 100;
    case "high":
      return 80;
    case "medium":
      return 60;
    case "low":
      return 40;
    default:
      return 0;
  }
};

const sortMetaFromInboxSort = (sort: InboxSort) => {
  if (sort === "priority") {
    return { sortBy: "priority", sortDir: "desc" as const };
  }
  if (sort === "deadline") {
    return { sortBy: "dueAt", sortDir: "asc" as const };
  }
  return { sortBy: "createdAt", sortDir: "desc" as const };
};

const sortTasks = (items: Task[], sort?: InboxSort) => {
  if (!sort) {
    return items;
  }
  const copy = [...items];
  switch (sort) {
    case "priority":
      return copy.sort((a, b) => priorityWeight(b.priority) - priorityWeight(a.priority));
    case "deadline":
      return copy.sort((a, b) => {
        const aDate = a.dueAt ?? a.decision?.deadlineAt ?? "";
        const bDate = b.dueAt ?? b.decision?.deadlineAt ?? "";
        const aTime = aDate ? Date.parse(aDate) : Number.POSITIVE_INFINITY;
        const bTime = bDate ? Date.parse(bDate) : Number.POSITIVE_INFINITY;
        return aTime - bTime;
      });
    case "createdAt":
      return copy.sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt));
    default:
      return items;
  }
};

const filterTasks = (
  items: Task[],
  filter: {
    state?: TaskState;
    source?: string;
    assignee?: string;
    priority?: TaskPriority;
    search?: string;
    taskId?: string;
  }
) => {
  const matcher = (value?: string | null, term?: string) => {
    if (!term) {
      return true;
    }
    return value?.toLowerCase().includes(term.toLowerCase()) ?? false;
  };

  return items.filter((task) => {
    if (filter.taskId && task.id !== filter.taskId) {
      return false;
    }
    if (filter.state && task.state !== filter.state) {
      return false;
    }
    if (filter.source && task.source !== filter.source) {
      return false;
    }
    if (filter.assignee && task.assignee !== filter.assignee) {
      return false;
    }
    if (filter.priority !== undefined && task.priority !== filter.priority) {
      return false;
    }
    if (filter.search) {
      const match =
        matcher(task.summary ?? task.title, filter.search) ||
        matcher(task.entity?.label ?? ("label" in (task.entity ?? {}) ? (task.entity as { label?: string }).label : undefined), filter.search) ||
        matcher(task.entity?.type, filter.search);
      if (!match) {
        return false;
      }
    }
    return true;
  });
};

const buildSummary = (items: Task[]) => {
  const summary = {
    open: 0,
    inProgress: 0,
    blocked: 0,
  };
  items.forEach((task) => {
    if (task.state === "blocked") {
      summary.blocked += 1;
      summary.inProgress += 1;
      return;
    }
    if (task.state === "open") {
      summary.open += 1;
      return;
    }
    if (task.state === "in_progress" || task.state === "snoozed") {
      summary.inProgress += 1;
    }
  });
  return summary;
};

export async function GET(request: NextRequest) {
  const permission = await requirePermission("inbox", "view");
  if (!permission.ok) {
    return permission.response;
  }

  const params = request.nextUrl.searchParams;
  const page = parsePositiveInt(params.get("page"), 1);
  const limit = parsePositiveInt(params.get("pageSize") ?? params.get("limit"), 25);
  const state = parseString(params.get("state")) as TaskState | undefined;
  const source = parseString(params.get("source"));
  const assignee = parseString(params.get("assignee"));
  const search = parseString(params.get("search"));
  const taskId = parseString(params.get("taskId"));
  const priority = normalizePriority(parseString(params.get("priority")));
  const sort = (parseString(params.get("sort")) as InboxSort | undefined) ?? "priority";

  const filtered = filterTasks(MOCK_TASKS, { state, source, assignee, search, priority, taskId });
  if (taskId && filtered.length === 0) {
    return errorResponse(404, "NOT_FOUND", "Task not found.");
  }

  const sorted = sortTasks(filtered, sort);
  const total = sorted.length;
  const start = (page - 1) * limit;
  const items = sorted.slice(start, start + limit);

  return NextResponse.json({
    data: items,
    items,
    pagination: buildPaginationMeta(page, limit, total),
    sort: sortMetaFromInboxSort(sort),
    filters: { state, source, assignee, priority, search, taskId },
    summary: buildSummary(sorted),
  });
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
