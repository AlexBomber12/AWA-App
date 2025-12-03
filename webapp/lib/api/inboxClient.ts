import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiMutation } from "@/lib/api/useApiMutation";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";

import type { BffItemResponse, BffListResponse, Task, TaskSource, TaskState } from "./bffTypes";

export type InboxQuery = {
  page?: number;
  pageSize?: number;
  state?: TaskState | "all";
  source?: TaskSource;
  priority?: Task["priority"];
  assignee?: string;
  search?: string;
  taskId?: string;
  sort?: "priority" | "deadline" | "createdAt";
};

export type InboxListResponse = BffListResponse<Task> & {
  summary?: {
    open: number;
    inProgress: number;
    blocked: number;
  };
};

const INBOX_ENDPOINT = "/api/bff/inbox";

const buildInboxUrl = (query?: InboxQuery) => {
  const params = new URLSearchParams();
  if (query?.page) {
    params.set("page", String(query.page));
  }
  if (query?.pageSize) {
    params.set("pageSize", String(query.pageSize));
  }
  if (query?.state && query.state !== "all") {
    params.set("state", query.state);
  }
  if (query?.source) {
    params.set("source", query.source);
  }
  if (query?.priority !== undefined) {
    params.set("priority", String(query.priority));
  }
  if (query?.assignee) {
    params.set("assignee", query.assignee);
  }
  if (query?.search) {
    params.set("search", query.search);
  }
  if (query?.taskId) {
    params.set("taskId", query.taskId);
  }
  if (query?.sort) {
    params.set("sort", query.sort);
  }
  const suffix = params.toString();
  return suffix ? `${INBOX_ENDPOINT}?${params.toString()}` : INBOX_ENDPOINT;
};

export const inboxTasksQueryKey = (query?: InboxQuery) => ["inbox", "tasks", query] as const;
export const inboxTaskQueryKey = (taskId: string | null) => ["inbox", "task", taskId] as const;

export async function fetchInboxTasks(query?: InboxQuery, signal?: AbortSignal): Promise<InboxListResponse> {
  const url = buildInboxUrl(query);
  return fetchFromBff<InboxListResponse>(url, {
    method: "GET",
    signal,
  });
}
export const getInboxTasks = fetchInboxTasks;

export async function fetchTaskById(taskId: string, signal?: AbortSignal): Promise<Task | null> {
  const response = await fetchInboxTasks({ taskId, page: 1, pageSize: 1 }, signal);
  const items = response.data ?? response.items ?? [];
  return items[0] ?? null;
}

type UseInboxTasksOptions = Omit<
  UseApiQueryOptions<InboxListResponse, ApiError, InboxListResponse, ReturnType<typeof inboxTasksQueryKey>>,
  "queryKey" | "queryFn"
>;

export function useInboxTasks(query?: InboxQuery, options?: UseInboxTasksOptions) {
  return useApiQuery<InboxListResponse, ApiError, InboxListResponse, ReturnType<typeof inboxTasksQueryKey>>({
    queryKey: inboxTasksQueryKey(query),
    queryFn: ({ signal }) => fetchInboxTasks(query, signal),
    retry: options?.retry ?? 0,
    ...options,
  });
}

type UseTaskByIdOptions = Omit<
  UseApiQueryOptions<Task | null, ApiError, Task | null, ReturnType<typeof inboxTaskQueryKey>>,
  "queryKey" | "queryFn" | "enabled"
> & { enabled?: boolean };

export function useTaskById(taskId: string | null, options?: UseTaskByIdOptions) {
  const enabled = Boolean(taskId) && (options?.enabled ?? true);
  return useApiQuery<Task | null, ApiError, Task | null, ReturnType<typeof inboxTaskQueryKey>>({
    queryKey: inboxTaskQueryKey(taskId),
    queryFn: ({ signal }) => fetchTaskById(taskId ?? "", signal),
    enabled,
    ...options,
  });
}

export type TaskStateUpdate = {
  taskId: string;
  state: TaskState;
  nextRequestAt?: string | null;
};

const taskActionPath = (taskId: string, action: "apply" | "dismiss" | "snooze" | "undo") =>
  `${INBOX_ENDPOINT}/tasks/${taskId}/${action}`;

const runTaskMutation = async (taskId: string, action: Parameters<typeof taskActionPath>[1], body?: object): Promise<Task> => {
  const response = await fetchFromBff<BffItemResponse<Task>>(taskActionPath(taskId, action), {
    method: "POST",
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  return response.data;
};

export async function markTaskDone(taskId: string): Promise<Task> {
  return runTaskMutation(taskId, "apply");
}

export async function snoozeTask(taskId: string, nextRequestAt: string): Promise<Task> {
  return runTaskMutation(taskId, "snooze", { next_request_at: nextRequestAt });
}

export async function dismissTask(taskId: string): Promise<Task> {
  return runTaskMutation(taskId, "dismiss");
}

export async function undoTaskAction(taskId: string): Promise<Task> {
  return runTaskMutation(taskId, "undo");
}

export function useMarkTaskDoneMutation() {
  return useApiMutation<Task, ApiError, string>({
    mutationFn: (taskId) => markTaskDone(taskId),
  });
}

export function useSnoozeTaskMutation() {
  return useApiMutation<Task, ApiError, { taskId: string; nextRequestAt: string }>({
    mutationFn: ({ taskId, nextRequestAt }) => snoozeTask(taskId, nextRequestAt),
  });
}

export function useUndoTaskActionMutation() {
  return useApiMutation<Task, ApiError, string>({
    mutationFn: (taskId) => undoTaskAction(taskId),
  });
}

export function useDismissTaskMutation() {
  return useApiMutation<Task, ApiError, string>({
    mutationFn: (taskId) => dismissTask(taskId),
  });
}
