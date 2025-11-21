import type { DecisionPayload, DecisionPriority } from "./decisionTypes";

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
  source: TaskSource;
  entity: TaskEntity;
  summary: string;
  decision: DecisionPayload;
  priority: DecisionPriority;
  deadlineAt?: string;
  defaultAction?: string;
  why: DecisionPayload["why"];
  alternatives: DecisionPayload["alternatives"];
  nextRequestAt?: string;
  state: TaskState;
  assignee?: string;
  createdAt: string;
  updatedAt: string;
};
