"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { ErrorState, FilterBar } from "@/components/data";
import { PageBody, PageHeader } from "@/components/layout";
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui";
import type { InboxListResponse, InboxQuery } from "@/lib/api/inboxClient";
import { inboxTasksQueryKey, useInboxTasks } from "@/lib/api/inboxClient";
import type { Task, TaskSource, TaskState } from "@/lib/api/inboxTypes";
import type { DecisionPriority } from "@/lib/api/decisionTypes";

import { useActionFlow } from "@/components/hooks/useActionFlow";

import { InboxTable } from "./InboxTable";
import { TaskDetailsDrawer } from "./TaskDetailsDrawer";

const EMPTY_TASKS: Task[] = [];

type FilterState = {
  state: TaskState | "all";
  source: "" | TaskSource;
  priority: "" | Exclude<DecisionPriority, number>;
  search: string;
  assignee: string;
};

type InboxSort = NonNullable<InboxQuery["sort"]>;

const DEFAULT_FILTERS: FilterState = {
  state: "open",
  source: "",
  priority: "",
  search: "",
  assignee: "",
};

const cloneTaskResponse = (response: InboxListResponse): InboxListResponse => {
  const source = response.data ?? response.items ?? [];
  const items = source.map((task) => ({
    ...task,
    entity: task.entity ? { ...task.entity } : task.entity,
    decision: task.decision
      ? {
          ...task.decision,
          why: [...task.decision.why],
          alternatives: [...task.decision.alternatives],
        }
      : undefined,
  }));

  return {
    ...response,
    data: items,
    items,
  };
};

export function InboxPage() {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [draftFilters, setDraftFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [sort, setSort] = useState<InboxSort>("priority");
  const queryClient = useQueryClient();
  const { runAction, undoLastAction, canUndo, isRunning, lastActionLabel } = useActionFlow();

  const query = useMemo<InboxQuery>(
    () => ({
      page: 1,
      pageSize: 25,
      state: filters.state === "all" ? undefined : filters.state,
      source: filters.source || undefined,
      priority: filters.priority || undefined,
      search: filters.search.trim() || undefined,
      assignee: filters.assignee.trim() || undefined,
      sort,
    }),
    [filters, sort]
  );

  const queryKey = useMemo(() => inboxTasksQueryKey(query), [query]);
  const inboxQuery = useInboxTasks(query);

  const tasks = useMemo(() => inboxQuery.data?.data ?? inboxQuery.data?.items ?? EMPTY_TASKS, [inboxQuery.data]);
  const selectedTask = useMemo(() => tasks.find((task) => task.id === selectedTaskId), [tasks, selectedTaskId]);

  useEffect(() => {
    if (selectedTaskId && !selectedTask) {
      setDrawerOpen(false);
      setSelectedTaskId(null);
    }
  }, [selectedTaskId, selectedTask]);

  const isDirty =
    draftFilters.state !== filters.state ||
    draftFilters.source !== filters.source ||
    draftFilters.priority !== filters.priority ||
    draftFilters.search !== filters.search ||
    draftFilters.assignee !== filters.assignee;

  const applyFilters = () => setFilters(draftFilters);
  const resetFilters = () => {
    setDraftFilters(DEFAULT_FILTERS);
    setFilters(DEFAULT_FILTERS);
  };

  const updateTask = useCallback(
    (taskId: string, updater: (task: Task) => Task) => {
      const current = queryClient.getQueryData<InboxListResponse>(queryKey);
      if (!current) {
        return undefined;
      }
      const snapshot = cloneTaskResponse(current);
      const items = current.data ?? current.items ?? [];
      const nextItems = items.map((task) => (task.id === taskId ? updater(task) : task));
      queryClient.setQueryData(queryKey, { ...current, data: nextItems, items: nextItems });
      return () => queryClient.setQueryData(queryKey, snapshot);
    },
    [queryClient, queryKey]
  );

  const handleApply = useCallback(
    (task: Task) => {
      void runAction({
        label: "Mark task done",
        successMessage: "Task marked as done",
        errorMessage: "Unable to update task",
        undoLabel: "Reopen task",
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
        label: "Undo decision",
        successMessage: "Decision undone",
        errorMessage: "Unable to undo decision",
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

  const summary = inboxQuery.data?.summary;

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
        <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-900">
            Open: {summary?.open ?? 0}
          </span>
          <span className="rounded-full bg-sky-100 px-3 py-1 text-sky-900">
            In progress: {summary?.inProgress ?? 0}
          </span>
          <span className="rounded-full bg-orange-100 px-3 py-1 text-orange-900">
            Blocked: {summary?.blocked ?? 0}
          </span>
        </div>
      </PageHeader>
      <PageBody>
        <div className="space-y-6">
          <FilterBar onApply={applyFilters} onReset={resetFilters} isDirty={isDirty} disableActions={inboxQuery.isFetching}>
            <div className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">State</span>
              <Select
                value={draftFilters.state}
                onValueChange={(value) => setDraftFilters((current) => ({ ...current, state: value as FilterState["state"] }))}
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="State" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="in_progress">In progress</SelectItem>
                  <SelectItem value="snoozed">Snoozed</SelectItem>
                  <SelectItem value="blocked">Blocked</SelectItem>
                  <SelectItem value="done">Done</SelectItem>
                  <SelectItem value="cancelled">Cancelled</SelectItem>
                  <SelectItem value="all">All</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Source</span>
              <Select
                value={draftFilters.source || "all"}
                onValueChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    source: value === "all" ? "" : (value as TaskSource),
                  }))
                }
              >
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Source" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="decision_engine">Decision Engine</SelectItem>
                  <SelectItem value="email">Inbox email</SelectItem>
                  <SelectItem value="manual">Manual</SelectItem>
                  <SelectItem value="system">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Priority</span>
              <Select
                value={draftFilters.priority || "all"}
                onValueChange={(value) =>
                  setDraftFilters((current) => ({
                    ...current,
                    priority: value === "all" ? "" : (value as Exclude<DecisionPriority, number>),
                  }))
                }
              >
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Priority" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Assignee</span>
              <Input
                value={draftFilters.assignee}
                onChange={(event) => setDraftFilters((current) => ({ ...current, assignee: event.target.value }))}
                placeholder="Assignee"
                className="w-40"
              />
            </div>
            <div className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Search</span>
              <Input
                value={draftFilters.search}
                onChange={(event) => setDraftFilters((current) => ({ ...current, search: event.target.value }))}
                placeholder="Search summary or entity"
                className="w-64"
              />
            </div>
            <div className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Sort</span>
              <Select value={sort} onValueChange={(value) => setSort(value as InboxSort)}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Sort" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="priority">Priority</SelectItem>
                  <SelectItem value="deadline">Deadline</SelectItem>
                  <SelectItem value="createdAt">Created</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </FilterBar>
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
