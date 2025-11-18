"use client";

import { useMemo } from "react";

import { Button, Drawer, DrawerContent, DrawerDescription, DrawerFooter, DrawerHeader, DrawerTitle } from "@/components/ui";
import type { Task } from "@/lib/api/inboxClient";
import { PermissionGuard } from "@/lib/permissions/client";
import { cn } from "@/lib/utils";

import {
  TASK_PRIORITY_STYLES,
  TASK_STATE_STYLES,
  formatTaskDate,
  formatTaskEntity,
  formatTaskPriority,
  formatTaskSource,
  formatTaskState,
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
    return [
      { label: "Entity", value: `${formatTaskEntity(task.entity)} · ${task.entity.type}` },
      { label: "Source", value: formatTaskSource(task.source) },
      { label: "Assignee", value: task.assignee ?? "Unassigned" },
      { label: "Due", value: formatTaskDate(task.due) },
      { label: "Created", value: formatTaskDate(task.createdAt) },
      { label: "Updated", value: formatTaskDate(task.updatedAt) },
    ];
  }, [task]);

  if (!task) {
    return null;
  }

  return (
    <Drawer open={isOpen} onOpenChange={(open) => (!open ? onClose() : undefined)}>
      <DrawerContent className="max-w-lg">
        <DrawerHeader>
          <DrawerTitle className="text-xl">{task.summary}</DrawerTitle>
          <DrawerDescription>Review and resolve the decision from Decision Engine.</DrawerDescription>
        </DrawerHeader>
        <div className="flex flex-1 flex-col gap-6 overflow-y-auto py-4">
          <div className="space-y-3 rounded-xl border border-border bg-muted/20 p-4">
            <SectionTitle>Task</SectionTitle>
            <div className="flex flex-wrap gap-2">
              <span className={cn("rounded-full px-3 py-1 text-xs font-semibold uppercase", TASK_STATE_STYLES[task.state])}>
                {formatTaskState(task.state)}
              </span>
              <span
                className={cn(
                  "rounded-full px-3 py-1 text-xs font-semibold uppercase",
                  TASK_PRIORITY_STYLES[task.decision.priority]
                )}
              >
                {formatTaskPriority(task.decision.priority)} priority
              </span>
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
            <div className="space-y-2 text-sm">
              <p>
                <span className="font-semibold text-foreground">Action:</span>{" "}
                {task.decision.decision.replaceAll("_", " ")}
              </p>
              {task.decision.deadlineAt ? (
                <p>
                  <span className="font-semibold text-foreground">Deadline:</span> {formatTaskDate(task.decision.deadlineAt)}
                </p>
              ) : null}
              {task.decision.defaultAction ? (
                <p>
                  <span className="font-semibold text-foreground">Default action:</span> {task.decision.defaultAction}
                </p>
              ) : null}
              {task.decision.nextRequestAt ? (
                <p>
                  <span className="font-semibold text-foreground">Next request:</span> {formatTaskDate(task.decision.nextRequestAt)}
                </p>
              ) : null}
            </div>

            <div className="space-y-2">
              <p className="text-sm font-semibold">Why</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {task.decision.why.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>

            <div className="space-y-2">
              <p className="text-sm font-semibold">Alternatives</p>
              <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                {task.decision.alternatives.map((alt) => (
                  <li key={alt}>{alt}</li>
                ))}
              </ul>
            </div>
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
                  Apply decision
                </Button>
                <Button variant="outline" onClick={() => onDecline(task)} isLoading={isActionPending}>
                  Decline
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
