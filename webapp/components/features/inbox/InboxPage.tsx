"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/data";
import { PageBody, PageHeader } from "@/components/layout";
import { Button } from "@/components/ui";
import type { InboxListResponse, Task } from "@/lib/api/inboxClient";
import { inboxListQueryKey, useInboxListQuery } from "@/lib/api/inboxClient";

import { useActionFlow } from "@/components/hooks/useActionFlow";

import { InboxTable } from "./InboxTable";
import { TaskDetailsDrawer } from "./TaskDetailsDrawer";

const EMPTY_TASKS: Task[] = [];

const cloneTaskResponse = (response: InboxListResponse) => ({
  ...response,
  items: response.items.map((task) => ({
    ...task,
    entity: { ...task.entity },
    decision: {
      ...task.decision,
      why: [...task.decision.why],
      alternatives: [...task.decision.alternatives],
    },
  })),
});

export function InboxPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const inboxQuery = useInboxListQuery();
  const queryClient = useQueryClient();
  const { runAction, undoLastAction, canUndo, isRunning, lastActionLabel } = useActionFlow();

  const tasks = useMemo(() => inboxQuery.data?.items ?? EMPTY_TASKS, [inboxQuery.data]);
  const selectedTask = useMemo(() => tasks.find((task) => task.id === selectedTaskId), [tasks, selectedTaskId]);

  useEffect(() => {
    if (selectedTaskId && !selectedTask) {
      setDrawerOpen(false);
      setSelectedTaskId(null);
    }
  }, [selectedTaskId, selectedTask]);

  const updateTask = useCallback(
    (taskId: string, updater: (task: Task) => Task) => {
      const current = queryClient.getQueryData<InboxListResponse>(inboxListQueryKey);
      if (!current) {
        return undefined;
      }
      const snapshot = cloneTaskResponse(current);
      const nextItems = current.items.map((task) => (task.id === taskId ? updater(task) : task));
      queryClient.setQueryData(inboxListQueryKey, { ...current, items: nextItems });
      return () => queryClient.setQueryData(inboxListQueryKey, snapshot);
    },
    [queryClient]
  );

  const handleApply = useCallback(
    (task: Task) => {
      void runAction({
        label: "Apply decision",
        successMessage: "Task applied",
        errorMessage: "Unable to apply task",
        optimisticUpdate: () =>
          updateTask(task.id, (current) => ({
            ...current,
            state: "done",
            updatedAt: new Date().toISOString(),
          })),
      });
    },
    [runAction, updateTask]
  );

  const handleDecline = useCallback(
    (task: Task) => {
      void runAction({
        label: "Decline task",
        successMessage: "Task declined",
        errorMessage: "Unable to decline task",
        optimisticUpdate: () =>
          updateTask(task.id, (current) => ({
            ...current,
            state: "cancelled",
            updatedAt: new Date().toISOString(),
          })),
      });
    },
    [runAction, updateTask]
  );

  const handleSnooze = useCallback(
    (task: Task) => {
      const nextFollowUp = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
      void runAction({
        label: "Snooze task",
        successMessage: "Task snoozed for 24h",
        errorMessage: "Unable to snooze task",
        optimisticUpdate: () =>
          updateTask(task.id, (current) => ({
            ...current,
            state: "snoozed",
            updatedAt: new Date().toISOString(),
            decision: {
              ...current.decision,
              nextRequestAt: nextFollowUp,
            },
          })),
      });
    },
    [runAction, updateTask]
  );

  const handleSelectTask = (task: Task) => {
    setSelectedTaskId(task.id);
    setDrawerOpen(true);
  };

  const handleCloseDrawer = () => {
    setDrawerOpen(false);
    setSelectedTaskId(null);
  };

  const openCount = useMemo(() => tasks.filter((task) => task.state === "open").length, [tasks]);

  return (
    <>
      <PageHeader
        title="Inbox"
        description="Operator triage workspace for Decision Engine, ROI, and buyer workflows."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Inbox", active: true },
        ]}
        actions={
          <Button variant="outline" onClick={() => inboxQuery.refetch()} isLoading={inboxQuery.isFetching}>
            Refresh
          </Button>
        }
      >
        <p className="text-sm text-muted-foreground">Open tasks: {openCount}</p>
      </PageHeader>
      <PageBody>
        <div className="space-y-6">
          {inboxQuery.error ? (
            <ErrorState title="Unable to load inbox" error={inboxQuery.error} onRetry={() => inboxQuery.refetch()} />
          ) : null}
          <InboxTable
            tasks={tasks}
            isLoading={inboxQuery.isPending || inboxQuery.isFetching}
            onSelectTask={handleSelectTask}
            selectedTaskId={selectedTaskId}
          />
        </div>
        <TaskDetailsDrawer
          task={selectedTask}
          isOpen={drawerOpen && Boolean(selectedTask)}
          onClose={handleCloseDrawer}
          onApply={handleApply}
          onDecline={handleDecline}
          onSnooze={handleSnooze}
          canUndo={canUndo}
          onUndo={undoLastAction}
          isActionPending={isRunning}
          lastActionLabel={lastActionLabel}
        />
      </PageBody>
    </>
  );
}
