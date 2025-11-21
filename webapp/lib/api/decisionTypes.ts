export type DecisionAction =
  | "request_price"
  | "update_price"
  | "request_discount"
  | "switch_vendor"
  | "review_uom"
  | "wait_until"
  | "continue"
  | "blocked_observe";

export type DecisionPriority = "low" | "medium" | "high" | "critical" | number;

export type DecisionReason = {
  title: string;
  detail?: string;
  code?: string;
  metric?: string;
} | string;

export type DecisionAlternative = {
  decision: DecisionAction;
  label?: string;
  defaultAction?: string;
  why?: DecisionReason[];
  impact?: string;
};

export type DecisionMetrics = {
  roi?: number;
  riskAdjustedRoi?: number;
  maxCogs?: number;
  revenueDelta?: number;
  marginDelta?: number;
};

export type DecisionPayload = {
  decision: DecisionAction;
  priority: DecisionPriority;
  deadlineAt?: string;
  defaultAction?: string;
  why: DecisionReason[];
  alternatives: DecisionAlternative[];
  nextRequestAt?: string;
  metrics?: DecisionMetrics;
};

export type RuleScope = "category" | "vendor" | "sku" | "global" | "campaign";

export type RuleCondition = {
  field?: string;
  operator?: string;
  value?: string | number | boolean | (string | number | boolean)[];
  category?: string;
  vendorId?: string;
  asin?: string;
  cadenceDays?: number;
  expression?: string;
  observeOnly?: boolean;
  campaignId?: string;
};

export type RuleAction = {
  action: DecisionAction;
  cadenceDays?: number;
  params?: Record<string, unknown>;
  defaultAction?: string;
  undoWindowHours?: number;
};

export type Rule = {
  id: string;
  name: string;
  scope: RuleScope;
  description?: string;
  conditions: RuleCondition[];
  actions: RuleAction[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
  cadence?: {
    type: "rolling" | "calendar";
    days: number;
  };
};

export type SimulationInput = {
  price?: number;
  cost?: number;
  volatility?: number;
  category?: string;
  observeOnly?: boolean;
  [key: string]: string | number | boolean | undefined | null;
};

export type SimulationMetrics = {
  roi?: number;
  riskAdjustedRoi?: number;
  maxCogs?: number;
  revenueImpact?: number;
  cogsCeiling?: number;
};

export type SimulationScenario = {
  id: string;
  name: string;
  description?: string;
  ruleId: string;
  input: SimulationInput;
  metrics?: SimulationMetrics;
  decisions: DecisionPayload[];
  createdAt: string;
  updatedAt?: string;
};
