import type { Meta, StoryObj } from "@storybook/react";

import { InboxTable } from "@/components/features/inbox/InboxTable";
import type { Task } from "@/lib/api/inboxClient";

const MOCK_TASKS: Task[] = [
  {
    id: "task-story-1",
    source: "decision_engine",
    entity: { type: "sku", id: "SKU-001", asin: "B00STORY1", label: "Story Yoga Mat" },
    summary: "Apply updated ROI guardrail",
    assignee: "Story Admin",
    due: new Date().toISOString(),
    state: "open",
    decision: {
      decision: "update_price",
      priority: "high",
      deadlineAt: new Date().toISOString(),
      defaultAction: "Increase price by 1%",
      why: ["ROI under 15% threshold", "Competitor price raised"],
      alternatives: ["Request discount", "Wait until next cycle"],
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "task-story-2",
    source: "manual",
    entity: { type: "vendor", id: "VEND-22", vendorId: "22", label: "Northwind Foods" },
    summary: "Follow up on onboarding checklist",
    assignee: "Jordan",
    due: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
    state: "in_progress",
    decision: {
      decision: "continue",
      priority: "medium",
      deadlineAt: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
      defaultAction: "Complete onboarding tasks",
      why: ["Missing W-9", "Need ACH form"],
      alternatives: ["Escalate to legal"],
    },
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
