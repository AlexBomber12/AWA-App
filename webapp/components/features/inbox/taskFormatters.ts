import type { Task, TaskEntity } from "@/lib/api/inboxClient";

export const TASK_STATE_STYLES: Record<Task["state"], string> = {
  open: "bg-emerald-100 text-emerald-900",
  in_progress: "bg-sky-100 text-sky-900",
  done: "bg-zinc-200 text-zinc-900",
  snoozed: "bg-amber-100 text-amber-900",
  cancelled: "bg-rose-100 text-rose-900",
};

export const TASK_PRIORITY_STYLES: Record<Task["decision"]["priority"], string> = {
  high: "bg-rose-100 text-rose-900",
  medium: "bg-amber-100 text-amber-900",
  low: "bg-emerald-100 text-emerald-900",
};

export const formatTaskState = (state: Task["state"]) =>
  ({
    open: "Open",
    in_progress: "In progress",
    done: "Done",
    snoozed: "Snoozed",
    cancelled: "Cancelled",
  })[state];

export const formatTaskPriority = (priority: Task["decision"]["priority"]) =>
  ({
    high: "High",
    medium: "Medium",
    low: "Low",
  })[priority];

export const formatTaskSource = (source: Task["source"]) =>
  ({
    decision_engine: "Decision Engine",
    inbox_email: "Inbox email",
    manual: "Manual",
    system: "System",
  })[source] ?? source;

export const formatTaskDate = (value?: string, includeTime = true) => {
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
  const label = entity.label ?? entity.id;
  if (entity.type === "sku" && entity.asin) {
    return `${label} (${entity.asin})`;
  }
  if (entity.type === "vendor" && entity.vendorId) {
    return `${label} (Vendor ${entity.vendorId})`;
  }
  return label;
};
