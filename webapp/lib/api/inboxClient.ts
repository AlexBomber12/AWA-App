import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";

export type TaskState = "open" | "in_progress" | "done" | "snoozed" | "cancelled";
export type TaskSource = "decision_engine" | "inbox_email" | "manual" | "system";

export type TaskEntity =
  | {
      type: "sku";
      id: string;
      asin?: string;
      label?: string;
    }
  | {
      type: "vendor";
      id: string;
      vendorId?: string;
      label?: string;
    }
  | {
      type: "price_list";
      id: string;
      label?: string;
    };

export type TaskDecision = {
  decision:
    | "request_price"
    | "update_price"
    | "request_discount"
    | "switch_vendor"
    | "review_uom"
    | "wait_until"
    | "continue"
    | "blocked_observe";
  priority: "low" | "medium" | "high";
  deadlineAt?: string;
  defaultAction?: string;
  why: string[];
  alternatives: string[];
  nextRequestAt?: string;
};

export type Task = {
  id: string;
  source: TaskSource;
  entity: TaskEntity;
  summary: string;
  assignee?: string;
  due?: string;
  state: TaskState;
  decision: TaskDecision;
  createdAt: string;
  updatedAt: string;
};

export type InboxListResponse = {
  items: Task[];
  total: number;
};

const INBOX_ENDPOINT = "/api/bff/inbox";

export const inboxListQueryKey = ["inbox", "list"] as const;

export async function fetchInboxList(signal?: AbortSignal): Promise<InboxListResponse> {
  return fetchFromBff<InboxListResponse>(INBOX_ENDPOINT, {
    method: "GET",
    signal,
  });
}

type UseInboxListQueryOptions = Omit<
  UseApiQueryOptions<InboxListResponse, ApiError, InboxListResponse, typeof inboxListQueryKey>,
  "queryKey" | "queryFn"
>;

export function useInboxListQuery(options?: UseInboxListQueryOptions) {
  return useApiQuery<InboxListResponse, ApiError, InboxListResponse, typeof inboxListQueryKey>({
    queryKey: inboxListQueryKey,
    queryFn: ({ signal }) => fetchInboxList(signal),
    ...options,
  });
}
