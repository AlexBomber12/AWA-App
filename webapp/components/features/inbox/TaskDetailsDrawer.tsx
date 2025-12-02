"use client";

import { useMemo } from "react";

import { Button, Drawer, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle } from "@/components/ui";
import type { Task } from "@/lib/api/inboxTypes";
import { PermissionGuard } from "@/lib/permissions/client";
import { cn } from "@/lib/utils";

import {
  TASK_STATE_STYLES,
  formatDecisionLabel,
  formatTaskDate,
  formatTaskEntity,
  formatTaskPriority,
  formatTaskSource,
  formatTaskState,
  reasonToText,
  taskPriorityStyle,
} from "./taskFormatters";

type TaskDetailsDrawerProps = {
  task?: Task | null;
  isOpen: boolean;
  onClose: () => void;
  onApply: (task: Task) => void;
  onDecline: (task: Task) => void;
  onSnooze: (task: Task) => void;
  canUndo: boolean;
  onUndo: () => void;
  isActionPending?: boolean;
  lastActionLabel?: string;
};

const SectionTitle = ({ children }: { children: React.ReactNode }) => (
  <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">{children}</p>
);

export function TaskDetailsDrawer({
  task,
  isOpen,
  onClose,
  onApply,
  onDecline,
  onSnooze,
  canUndo,
  onUndo,
  isActionPending,
  lastActionLabel,
}: TaskDetailsDrawerProps) {
  const metadata = useMemo(() => {
    if (!task) {
      return [];
    }
    const deadline = task.deadlineAt ?? task.dueAt ?? task.decision?.deadlineAt ?? null;
    const entityLabel = task.entity ? `${formatTaskEntity(task.entity)} · ${task.entity.type}` : "No entity";
    const nextRequest = task.nextRequestAt ?? task.decision?.nextRequestAt ?? null;

    return [
      { label: "Entity", value: entityLabel },
      { label: "Source", value: formatTaskSource(task.source) },
      { label: "Assignee", value: task.assignee ?? "Unassigned" },
      { label: "Deadline", value: formatTaskDate(deadline) },
      { label: "Next request", value: formatTaskDate(nextRequest) },
      { label: "Created", value: formatTaskDate(task.createdAt) },
      { label: "Updated", value: formatTaskDate(task.updatedAt) },
    ];
  }, [task]);

  if (!task) {
    return null;
  }

  const reasons = task.why?.length ? task.why : task.decision?.why ?? [];
  const alternatives = task.alternatives?.length ? task.alternatives : task.decision?.alternatives ?? [];
  const metrics = task.decision?.metrics;
  const decision = task.decision;

  return (
    <Drawer open={isOpen} onOpenChange={(open) => (!open ? onClose() : undefined)}>
      <DrawerContent className="max-w-lg">
        <DrawerHeader>
          <DrawerTitle className="text-xl">{task.summary}</DrawerTitle>
          <DrawerDescription>Review the virtual buyer recommendation and decide how to proceed.</DrawerDescription>
        </DrawerHeader>
        <div className="flex flex-1 flex-col gap-6 overflow-y-auto py-4">
          <div className="space-y-3 rounded-xl border border-border bg-muted/20 p-4">
            <SectionTitle>Task</SectionTitle>
            <div className="flex flex-wrap gap-2">
              <span
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-semibold uppercase",
                  TASK_STATE_STYLES[task.state ?? "open"] ?? TASK_STATE_STYLES.open
                )}
              >
                {formatTaskState(task.state ?? "open")}
              </span>
              <span
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-semibold uppercase",
                  taskPriorityStyle(task.priority ?? task.decision?.priority ?? "medium")
                )}
              >
                {formatTaskPriority(task.priority ?? task.decision?.priority ?? "medium")} priority
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
            </div>
            <dl className="grid grid-cols-1 gap-2 text-sm text-muted-foreground">
              {metadata.map((item) => (
                <div key={item.label}>
                  <dt className="font-semibold text-foreground">{item.label}</dt>
                  <dd>{item.value}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="space-y-4 rounded-xl border border-border bg-background p-4">
            <SectionTitle>Decision</SectionTitle>
            {decision ? (
              <>
                <div className="space-y-2 text-sm">
                  <p className="text-lg font-semibold capitalize">{formatDecisionLabel(decision.decision)}</p>
                  {decision.defaultAction ? (
                    <p className="text-sm text-muted-foreground">{decision.defaultAction}</p>
                  ) : null}
                </div>

                {metrics ? (
                  <div className="grid gap-3 sm:grid-cols-3">
                    {metrics.roi !== undefined ? (
                      <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                        <p className="text-xs uppercase text-muted-foreground">ROI</p>
                        <p className="text-lg font-semibold">{metrics.roi.toFixed(1)}%</p>
                      </div>
                    ) : null}
                    {metrics.riskAdjustedRoi !== undefined ? (
                      <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                        <p className="text-xs uppercase text-muted-foreground">Risk-adjusted ROI</p>
                        <p className="text-lg font-semibold">{metrics.riskAdjustedRoi.toFixed(1)}%</p>
                      </div>
                    ) : null}
                    {metrics.maxCogs !== undefined ? (
                      <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                        <p className="text-xs uppercase text-muted-foreground">Max COGS</p>
                        <p className="text-lg font-semibold">${metrics.maxCogs.toFixed(2)}</p>
                      </div>
                    ) : null}
                  </div>
                ) : null}

                <div className="space-y-2">
                  <p className="text-sm font-semibold">Why</p>
                  <ul className="space-y-2">
                    {reasons.map((reason, index) => (
                      <li
                        key={`${reasonToText(reason)}-${index}`}
                        className="flex items-start gap-2 rounded-md bg-muted/30 p-2 text-sm"
                      >
                        <span className="mt-0.5 text-xs text-muted-foreground">●</span>
                        <span className="text-muted-foreground">{reasonToText(reason)}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-2">
                  <p className="text-sm font-semibold">Alternatives</p>
                  <div className="flex flex-wrap gap-2">
                    {alternatives.map((alt, index) => (
                      <span
                        key={`${alt.decision}-${index}`}
                        className="rounded-full border border-border bg-muted/30 px-3 py-1 text-xs font-semibold"
                      >
                        {formatDecisionLabel(alt.decision)}
                        {alt.label ? ` — ${alt.label}` : ""}
                      </span>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No decision provided.</p>
            )}
          </div>
        </div>

        <DrawerFooter>
          <PermissionGuard
            resource="inbox"
            action="configure"
            fallback={
              <p className="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
                You do not have permission to take action on this task.
              </p>
            }
          >
            <div className="flex flex-col gap-2">
              <div className="flex flex-wrap gap-2">
                <Button onClick={() => onApply(task)} isLoading={isActionPending}>
                  Mark as done
                </Button>
                <Button variant="outline" onClick={() => onDecline(task)} isLoading={isActionPending}>
                  Undo decision
                </Button>
                <Button variant="secondary" onClick={() => onSnooze(task)} isLoading={isActionPending}>
                  Snooze
                </Button>
              </div>
              <Button variant="ghost" onClick={onUndo} disabled={!canUndo}>
                Undo last action {lastActionLabel ? `(${lastActionLabel})` : ""}
              </Button>
            </div>
          </PermissionGuard>
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </DrawerFooter>
      </DrawerContent>
    </Drawer>
  );
}
