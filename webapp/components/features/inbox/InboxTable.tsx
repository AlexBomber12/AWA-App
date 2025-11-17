"use client";

import { type ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";

import { DataTable, EmptyState } from "@/components/data";
import type { Task } from "@/lib/api/inboxClient";
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

type InboxTableProps = {
  tasks: Task[];
  isLoading?: boolean;
  onSelectTask?: (task: Task) => void;
  selectedTaskId?: string | null;
};

export function InboxTable({ tasks, isLoading, onSelectTask, selectedTaskId }: InboxTableProps) {
  const columns = useMemo<ColumnDef<Task>[]>(
    () => [
      {
        header: "State",
        accessorKey: "state",
        cell: ({ row }) => {
          const state = row.original.state;
          return (
            <span className={cn("rounded-full px-2 py-1 text-xs font-semibold uppercase", TASK_STATE_STYLES[state])}>
              {formatTaskState(state)}
            </span>
          );
        },
      },
      {
        header: "Priority",
        accessorKey: "decision.priority",
        cell: ({ row }) => {
          const priority = row.original.decision.priority;
          return (
            <span className={cn("rounded-full px-2 py-1 text-xs font-semibold uppercase", TASK_PRIORITY_STYLES[priority])}>
              {formatTaskPriority(priority)}
            </span>
          );
        },
      },
      {
        header: "Summary",
        accessorKey: "summary",
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{row.original.summary}</span>
            <span className="text-xs text-muted-foreground">{formatTaskState(row.original.state)}</span>
          </div>
        ),
      },
      {
        header: "Entity",
        accessorKey: "entity",
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{formatTaskEntity(row.original.entity)}</span>
            <span className="text-xs uppercase text-muted-foreground">{row.original.entity.type}</span>
          </div>
        ),
      },
      {
        header: "Source",
        accessorKey: "source",
        cell: ({ row }) => <span className="text-sm">{formatTaskSource(row.original.source)}</span>,
      },
      {
        header: "Assignee",
        accessorKey: "assignee",
        cell: ({ row }) => row.original.assignee ?? "Unassigned",
      },
      {
        header: "Due",
        accessorKey: "due",
        cell: ({ row }) => formatTaskDate(row.original.due),
      },
      {
        header: "Updated",
        accessorKey: "updatedAt",
        cell: ({ row }) => formatTaskDate(row.original.updatedAt),
      },
    ],
    []
  );

  const emptyState = (
    <EmptyState
      title="No tasks in the inbox"
      description="As soon as Decision Engine or inbox workflows emit tasks, they will appear here."
    />
  );

  return (
    <DataTable
      data={tasks}
      columns={columns}
      isLoading={isLoading}
      emptyState={emptyState}
      onRowClick={onSelectTask}
      rowKey={(task) => `${task.id}${selectedTaskId === task.id ? "-selected" : ""}`}
    />
  );
}
