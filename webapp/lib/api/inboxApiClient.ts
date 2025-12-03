import { fetchFromApi } from "@/lib/api/fetchFromApi";

import type { components, paths } from "./types.generated";

type InboxListResponse = paths["/inbox/tasks"]["get"]["responses"]["200"]["content"]["application/json"];
type TaskUpdatePayload = components["schemas"]["TaskUpdateRequest"] | null;
type DecisionTaskResponse = components["schemas"]["DecisionTask"];

export type InboxApiListParams = {
  page?: number;
  pageSize?: number;
  state?: string | null;
  status?: string | null;
  source?: string | null;
  priority?: number | null;
  assignee?: string | null;
  search?: string | null;
  taskId?: string | null;
  sort?: string | null;
};

const buildQuery = (params: InboxApiListParams): string => {
  const query = new URLSearchParams();
  if (params.page) {
    query.set("page", String(params.page));
  }
  if (params.pageSize) {
    query.set("pageSize", String(params.pageSize));
  }
  if (params.state) {
    query.set("state", params.state);
  }
  if (params.status) {
    query.set("status", params.status);
  }
  if (params.source) {
    query.set("source", params.source);
  }
  if (typeof params.priority === "number") {
    query.set("priority", String(params.priority));
  }
  if (params.assignee) {
    query.set("assignee", params.assignee);
  }
  if (params.search) {
    query.set("search", params.search);
  }
  if (params.taskId) {
    query.set("taskId", params.taskId);
  }
  if (params.sort) {
    query.set("sort", params.sort);
  }

  const suffix = query.toString();
  return suffix ? `?${suffix}` : "";
};

const postTaskUpdate = async (path: string, payload: TaskUpdatePayload): Promise<DecisionTaskResponse> => {
  const response = await fetchFromApi<DecisionTaskResponse>(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: payload ? JSON.stringify(payload) : undefined,
  });
  return response;
};

export const inboxApiClient = {
  async listTasks(params: InboxApiListParams = {}): Promise<InboxListResponse> {
    const query = buildQuery(params);
    return fetchFromApi<InboxListResponse>(`/inbox/tasks${query}`);
  },

  applyTask(taskId: string, payload: TaskUpdatePayload = null) {
    return postTaskUpdate(`/inbox/tasks/${taskId}/apply`, payload);
  },

  dismissTask(taskId: string, payload: TaskUpdatePayload = null) {
    return postTaskUpdate(`/inbox/tasks/${taskId}/dismiss`, payload);
  },

  snoozeTask(taskId: string, payload: TaskUpdatePayload = null) {
    return postTaskUpdate(`/inbox/tasks/${taskId}/snooze`, payload);
  },

  undoTask(taskId: string, payload: TaskUpdatePayload = null) {
    return postTaskUpdate(`/inbox/tasks/${taskId}/undo`, payload);
  },
};
