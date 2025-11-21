import type { Meta, StoryObj } from "@storybook/react";

import { InboxTable } from "@/components/features/inbox/InboxTable";
import type { Task } from "@/lib/api/inboxTypes";

const MOCK_TASKS: Task[] = [
  {
    id: "task-story-1",
    source: "decision_engine",
    entity: { type: "sku_vendor", asin: "B00STORY1", vendorId: "2042", label: "Story Yoga Mat" },
    summary: "Apply updated ROI guardrail",
    assignee: "Story Admin",
    state: "open",
    decision: {
      decision: "update_price",
      priority: 95,
      deadlineAt: new Date().toISOString(),
      defaultAction: "Increase price by 1%",
      why: ["ROI under 15% threshold", { title: "Competitor move", detail: "Competitor price raised" }],
      alternatives: [
        { decision: "request_discount", label: "Request vendor support" },
        { decision: "wait_until", label: "Wait until next cycle" },
      ],
    },
    priority: 95,
    deadlineAt: new Date().toISOString(),
    why: ["ROI under 15% threshold", { title: "Competitor move", detail: "Competitor price raised" }],
    alternatives: [
      { decision: "request_discount", label: "Request vendor support" },
      { decision: "wait_until", label: "Wait until next cycle" },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "task-story-2",
    source: "manual",
    entity: { type: "vendor", vendorId: "22", label: "Northwind Foods" },
    summary: "Follow up on onboarding checklist",
    assignee: "Jordan",
    state: "in_progress",
    decision: {
      decision: "continue",
      priority: "medium",
      deadlineAt: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Complete onboarding tasks",
      why: ["Missing W-9", "Need ACH form"],
      alternatives: [{ decision: "wait_until", label: "Escalate to legal" }],
    },
    priority: "medium",
    deadlineAt: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
    why: ["Missing W-9", "Need ACH form"],
    alternatives: [{ decision: "wait_until", label: "Escalate to legal" }],
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

const meta: Meta<typeof InboxTable> = {
  title: "Features/Inbox/InboxTable",
  component: InboxTable,
  args: {
    tasks: MOCK_TASKS,
    isLoading: false,
  },
};

export default meta;

type Story = StoryObj<typeof InboxTable>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    tasks: [],
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    tasks: [],
    isLoading: false,
  },
};
