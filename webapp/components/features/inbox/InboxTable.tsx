"use client";

import { type ColumnDef } from "@tanstack/react-table";
import { useMemo } from "react";

import { DataTable, EmptyState } from "@/components/data";
import type { Task } from "@/lib/api/inboxTypes";
import { cn } from "@/lib/utils";

import {
  TASK_STATE_STYLES,
  formatDecisionLabel,
  formatTaskDate,
  formatTaskEntity,
  formatTaskPriority,
  formatTaskState,
  reasonToText,
  taskPriorityStyle,
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
        header: "Task",
        accessorKey: "summary",
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium">{row.original.summary}</span>
            <span className="text-xs text-muted-foreground">ID: {row.original.id}</span>
          </div>
        ),
      },
      {
        header: "Decision",
        accessorKey: "decision.decision",
        cell: ({ row }) => {
          const decision = row.original.decision;
          if (!decision) {
            return (
              <div className="flex flex-col">
                <span className="font-semibold text-muted-foreground">No decision</span>
                <span className="text-xs text-muted-foreground">Suggested action</span>
              </div>
            );
          }
          return (
            <div className="flex flex-col">
              <span className="font-semibold capitalize">{formatDecisionLabel(decision.decision)}</span>
              <span className="text-xs text-muted-foreground">{decision.defaultAction ?? "Suggested action"}</span>
            </div>
          );
        },
      },
      {
        header: "Priority",
        accessorKey: "priority",
        cell: ({ row }) => {
          const priority = row.original.priority ?? row.original.decision?.priority ?? "medium";
          return (
            <span className={cn("rounded-full px-2 py-1 text-xs font-semibold uppercase", taskPriorityStyle(priority))}>
              {formatTaskPriority(priority)}
            </span>
          );
        },
      },
      {
        header: "Entity",
        accessorKey: "entity",
        cell: ({ row }) => {
          const entity = row.original.entity;
          if (!entity) {
            return <span className="text-xs text-muted-foreground">No entity</span>;
          }
          return (
            <div className="flex flex-col">
              <span className="font-medium">{formatTaskEntity(entity)}</span>
              <span className="text-xs uppercase text-muted-foreground">{entity.type}</span>
            </div>
          );
        },
      },
      {
        header: "Deadline",
        accessorKey: "dueAt",
        cell: ({ row }) => formatTaskDate(row.original.dueAt ?? row.original.decision?.deadlineAt ?? null, false),
      },
      {
        header: "State",
        accessorKey: "state",
        cell: ({ row }) => {
          const state = row.original.state ?? "open";
          return (
            <span
              className={cn(
                "rounded-full px-2 py-1 text-xs font-semibold uppercase",
                TASK_STATE_STYLES[state] ?? TASK_STATE_STYLES.open
              )}
            >
              {formatTaskState(state)}
            </span>
          );
        },
      },
      {
        header: "Assignee",
        accessorKey: "assignee",
        cell: ({ row }) => row.original.assignee ?? "Unassigned",
      },
      {
        header: "Why",
        accessorKey: "why",
        cell: ({ row }) => {
          const reasons = row.original.why?.length ? row.original.why : row.original.decision?.why;
          const preview = reasons?.length ? reasonToText(reasons[0]) : "—";
          return <span className="text-sm text-muted-foreground line-clamp-2">{preview}</span>;
        },
      },
    ],
    []
  );

  const emptyState = (
    <EmptyState
      title="No tasks in the inbox"
      description="As soon as Decision Engine or virtual buyer workflows emit tasks, they will appear here."
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
