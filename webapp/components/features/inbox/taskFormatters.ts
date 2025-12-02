import type { DecisionPriority, DecisionReason } from "@/lib/api/decisionTypes";
import type { Task, TaskEntity, TaskState } from "@/lib/api/inboxTypes";

export const TASK_STATE_STYLES: Record<TaskState, string> = {
  open: "bg-emerald-100 text-emerald-900",
  in_progress: "bg-sky-100 text-sky-900",
  done: "bg-zinc-200 text-zinc-900",
  snoozed: "bg-amber-100 text-amber-900",
  cancelled: "bg-rose-100 text-rose-900",
  blocked: "bg-orange-100 text-orange-900",
};

const PRIORITY_CLASS_MAP: Record<string, string> = {
  critical: "bg-rose-100 text-rose-900",
  high: "bg-amber-100 text-amber-900",
  medium: "bg-sky-100 text-sky-900",
  low: "bg-emerald-100 text-emerald-900",
};

const priorityThresholdClass = (priority: number) => {
  if (priority >= 90) {
    return PRIORITY_CLASS_MAP.critical;
  }
  if (priority >= 70) {
    return PRIORITY_CLASS_MAP.high;
  }
  if (priority >= 40) {
    return PRIORITY_CLASS_MAP.medium;
  }
  return PRIORITY_CLASS_MAP.low;
};

export const taskPriorityStyle = (priority: DecisionPriority) => {
  if (typeof priority === "number") {
    return priorityThresholdClass(priority);
  }
  return PRIORITY_CLASS_MAP[priority] ?? PRIORITY_CLASS_MAP.medium;
};

export const formatTaskState = (state: TaskState) =>
  ({
    open: "Open",
    in_progress: "In progress",
    done: "Done",
    snoozed: "Snoozed",
    cancelled: "Cancelled",
    blocked: "Blocked",
  })[state];

export const formatTaskPriority = (priority: DecisionPriority) => {
  if (typeof priority === "number") {
    if (priority >= 90) {
      return "Critical";
    }
    if (priority >= 70) {
      return "High";
    }
    if (priority >= 40) {
      return "Medium";
    }
    return "Low";
  }
  return priority.replace("_", " ");
};

export const formatDecisionLabel = (decision: string) => decision.replaceAll("_", " ");

const SOURCE_LABELS: Record<NonNullable<Task["source"]>, string> = {
  decision_engine: "Decision Engine",
  email: "Inbox email",
  manual: "Manual",
  system: "System",
};

export const formatTaskSource = (source: Task["source"]) => {
  if (!source) {
    return "Unknown source";
  }
  return SOURCE_LABELS[source as NonNullable<Task["source"]>] ?? source;
};

export const formatTaskDate = (value?: string | null, includeTime = true) => {
  if (!value) {
    return "—";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "—";
  }
  const options: Intl.DateTimeFormatOptions = includeTime
    ? { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }
    : { month: "short", day: "numeric" };
  return new Intl.DateTimeFormat(undefined, options).format(date);
};

export const formatTaskEntity = (entity: TaskEntity) => {
  switch (entity.type) {
    case "sku":
      return `${entity.label ?? entity.asin} (${entity.asin})`;
    case "sku_vendor":
      return entity.label ?? `${entity.asin} · Vendor ${entity.vendorId}`;
    case "vendor":
      return entity.label ?? `Vendor ${entity.vendorId}`;
    case "thread":
      return entity.label ?? entity.subject ?? entity.threadId;
    case "price_list":
      return entity.label ?? entity.id;
    default:
      return "Unknown entity";
  }
};

export const reasonToText = (reason: DecisionReason): string => {
  if (typeof reason === "string") {
    return reason;
  }
  if (reason.detail) {
    return `${reason.title}: ${reason.detail}`;
  }
  return reason.title;
};
