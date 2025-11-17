import { NextRequest, NextResponse } from "next/server";

import type { InboxListResponse, Task } from "@/lib/api/inboxClient";

export const dynamic = "force-dynamic";

const MOCK_TASKS: Task[] = [
  {
    id: "task-001",
    source: "decision_engine",
    entity: {
      type: "sku",
      id: "SKU-001",
      asin: "B00OPS1001",
      label: "ACME Flex Yoga Mat",
    },
    summary: "Request refreshed price quote from vendor",
    assignee: "Tara Nguyen",
    due: new Date(Date.now() + 36 * 60 * 60 * 1000).toISOString(),
    state: "open",
    decision: {
      decision: "request_price",
      priority: "high",
      deadlineAt: new Date(Date.now() + 30 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Email vendor for updated quote",
      why: [
        "ROI guardrail dropped below 15%",
        "Last quote expired 12 hours ago",
      ],
      alternatives: ["Reassign to virtual buyer", "Switch vendor"],
      nextRequestAt: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
    },
    createdAt: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
  },
  {
    id: "task-002",
    source: "manual",
    entity: {
      type: "vendor",
      id: "VEND-442",
      vendorId: "442",
      label: "Northwind Foods",
    },
    summary: "Follow up on vendor onboarding documents",
    assignee: "Jordan Miles",
    due: new Date(Date.now() + 72 * 60 * 60 * 1000).toISOString(),
    state: "in_progress",
    decision: {
      decision: "continue",
      priority: "medium",
      defaultAction: "Complete onboarding checklist",
      why: ["Vendor submitted partial paperwork", "Awaiting W-9 verification"],
      alternatives: ["Escalate to legal"],
    },
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "task-003",
    source: "inbox_email",
    entity: {
      type: "price_list",
      id: "PL-902",
      label: "Outdoor Spring Promo",
    },
    summary: "Review UoM discrepancy for promo price list",
    state: "snoozed",
    decision: {
      decision: "review_uom",
      priority: "low",
      deadlineAt: new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Confirm units with vendor",
      why: ["Discovered mismatch between carton and unit pricing"],
      alternatives: ["Lock list until clarification"],
      nextRequestAt: new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString(),
    },
    createdAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 12 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "task-004",
    source: "system",
    entity: {
      type: "sku",
      id: "SKU-994",
      asin: "B00OPS1994",
      label: "LumenSmart LED Strip",
    },
    summary: "Approve ROI guardrail exception",
    assignee: "Priya Patel",
    due: new Date(Date.now() + 12 * 60 * 60 * 1000).toISOString(),
    state: "open",
    decision: {
      decision: "blocked_observe",
      priority: "high",
      deadlineAt: new Date(Date.now() + 10 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Pause price change",
      why: ["ROI fluctuating ±8% within last 24h", "Pending buyer review"],
      alternatives: ["Wait until next ingestion cycle"],
    },
    createdAt: new Date(Date.now() - 10 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
  },
  {
    id: "task-005",
    source: "decision_engine",
    entity: {
      type: "vendor",
      id: "VEND-301",
      vendorId: "301",
      label: "Evergreen Brands",
    },
    summary: "Switch vendor for low-performing SKU bundle",
    state: "done",
    decision: {
      decision: "switch_vendor",
      priority: "medium",
      why: ["Better landed cost from backup vendor", "Existing PO delayed"],
      alternatives: ["Request discount", "Wait until inbound shipment"],
    },
    createdAt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "task-006",
    source: "manual",
    entity: {
      type: "sku",
      id: "SKU-555",
      asin: "B00OPS1555",
      label: "Nimbus Smart Air Purifier",
    },
    summary: "Wait for virtual buyer follow-up",
    assignee: "Taylor Chen",
    state: "cancelled",
    decision: {
      decision: "wait_until",
      priority: "low",
      defaultAction: "Pause until simulation completes",
      why: ["Simulation results pending", "Awaiting ROI delta confirmation"],
      alternatives: ["Escalate to admin"],
      nextRequestAt: new Date(Date.now() + 6 * 60 * 60 * 1000).toISOString(),
    },
    createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(),
  },
];

const parsePositiveInt = (value: string | null, fallback: number, max?: number) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  const normalized = Math.floor(parsed);
  if (max && normalized > max) {
    return max;
  }
  return normalized;
};

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const page = parsePositiveInt(params.get("page"), 1);
  const limit = parsePositiveInt(params.get("limit"), MOCK_TASKS.length, MOCK_TASKS.length);
  const start = (page - 1) * limit;
  const items = MOCK_TASKS.slice(start, start + limit);

  const response: InboxListResponse = {
    items,
    total: MOCK_TASKS.length,
  };

  return NextResponse.json(response);
}
