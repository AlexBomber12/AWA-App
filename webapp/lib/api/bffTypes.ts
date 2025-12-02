import type {
  DecisionAlternative,
  DecisionPayload,
  DecisionPriority,
  DecisionReason,
  RuleAction,
  RuleScope,
} from "@/lib/api/decisionTypes";

export type PaginationMeta = {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

export type SortDirection = "asc" | "desc";

export type SortMeta = {
  sortBy?: string;
  sortDir?: SortDirection;
};

export type FilterMeta = Record<string, string | number | boolean | null | undefined>;

export type BffListResponse<T> = {
  data: T[];
  items?: T[];
  pagination: PaginationMeta;
  sort?: SortMeta;
  filters?: FilterMeta;
  summary?: Record<string, number>;
};

export type BffItemResponse<T> = {
  data: T;
};

export type BffErrorResponse = {
  error: {
    code: string;
    message: string;
    status?: number;
    details?: unknown;
  };
};

export type TaskStatus = "open" | "in_progress" | "completed" | "archived";
export type TaskPriority = "low" | "medium" | "high" | "critical";
export type TaskState = "open" | "in_progress" | "done" | "snoozed" | "cancelled" | "blocked";
export type TaskSource = "decision_engine" | "email" | "manual" | "system";

export type SkuEntity = {
  type: "sku";
  asin: string;
  sku?: string;
  vendorId?: string;
  label?: string;
  category?: string;
};

export type VendorEntity = {
  type: "vendor";
  vendorId: string;
  id?: string;
  label?: string;
};

export type SkuVendorEntity = {
  type: "sku_vendor";
  asin: string;
  vendorId: string;
  sku?: string;
  label?: string;
  category?: string;
};

export type ThreadEntity = {
  type: "thread";
  threadId: string;
  subject?: string;
  channel?: "email" | "slack";
  label?: string;
};

export type PriceListEntity = {
  type: "price_list";
  id: string;
  label?: string;
  category?: string;
};

export type TaskEntity = SkuEntity | VendorEntity | SkuVendorEntity | ThreadEntity | PriceListEntity;

export type Task = {
  id: string;
  type: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: string;
  updatedAt: string;
  dueAt?: string | null;
  decisionId?: string | null;
  assignee?: string | null;
  source?: TaskSource | string | null;
  tags?: string[];
  metadata?: Record<string, string | number | boolean | null>;
  entity?: TaskEntity;
  decision?: DecisionPayload;
  summary?: string;
  state?: TaskState;
  why?: DecisionReason[];
  alternatives?: DecisionAlternative[];
  nextRequestAt?: string | null;
};

export type RuleCondition = {
  field: string;
  op: string;
  value: unknown;
  category?: string;
  vendorId?: string;
  expression?: string;
  cadenceDays?: number;
  observeOnly?: boolean;
};

export type Rule = {
  id: string;
  name: string;
  description: string | null;
  conditions: RuleCondition[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
  scope?: RuleScope;
  actions?: RuleAction[];
  cadence?: {
    type: "rolling" | "calendar";
    days: number;
  };
};

export type SimulationResult = {
  roi: number;
  margin: number;
  breakEvenPrice?: number;
  riskAdjustedRoi?: number;
  maxCogs?: number;
  revenueImpact?: number;
};

export type SimulationScenario = {
  id: string;
  name: string;
  baselineSku: string;
  parameters: Record<string, string | number | boolean | null>;
  result: SimulationResult;
  createdAt: string;
  updatedAt?: string;
  ruleId?: string;
  description?: string | null;
  decisions?: DecisionPayload[];
};

export type RoiItem = {
  sku: string;
  asin: string;
  title: string;
  roi: number;
  margin: number;
  currency: string;
  buyPrice: number;
  sellPrice: number;
  salesRank?: number | null;
  category?: string | null;
  vendorId?: string | null;
  fees?: number | null;
  freight?: number | null;
  cost?: number | null;
};

export type ReturnStatus = "pending" | "approved" | "denied" | "paid";

export type ReturnItem = {
  returnId: string;
  asin: string;
  sku: string;
  reason: string;
  quantity: number;
  reimbursementAmount: number;
  currency: string;
  status: ReturnStatus;
  createdAt: string;
  updatedAt: string;
  title?: string | null;
  vendor?: string | null;
  avgRefundPerUnit?: number;
};

export type DecisionSummary = {
  rules: Rule[];
  scenarios: SimulationScenario[];
  tasks?: Task[];
};
