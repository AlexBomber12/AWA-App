import type { Meta, StoryObj } from "@storybook/react";
import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";

import { TaskDetailsDrawer } from "@/components/features/inbox/TaskDetailsDrawer";
import type { Task } from "@/lib/api/inboxTypes";

const mockTask: Task = {
  id: "drawer-task",
  type: "ROI_REVIEW",
  title: "Review price adjustment",
  description: "Review price adjustment for Story Drawer SKU.",
  status: "open",
  source: "decision_engine",
  entity: { type: "sku_vendor", asin: "B00DRAWER", vendorId: "300", label: "Story Drawer SKU" },
  summary: "Review price adjustment for Story Drawer SKU",
  assignee: "Story Admin",
  state: "open",
  decision: {
    decision: "request_price",
    priority: "critical",
    deadlineAt: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
    defaultAction: "Email vendor for refreshed quote",
    why: ["ROI dipped to 13%", { title: "Competitor inventory spike", detail: "Stockout risk rising" }],
    alternatives: [
      { decision: "wait_until", label: "Wait until ingestion" },
      { decision: "switch_vendor", label: "Switch vendor" },
    ],
    nextRequestAt: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
    metrics: {
      roi: 13.2,
      riskAdjustedRoi: 11.4,
      maxCogs: 14.5,
    },
  },
  priority: "critical",
  deadlineAt: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
  nextRequestAt: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
  why: ["ROI dipped to 13%", { title: "Competitor inventory spike", detail: "Stockout risk rising" }],
  alternatives: [
    { decision: "wait_until", label: "Wait until ingestion" },
    { decision: "switch_vendor", label: "Switch vendor" },
  ],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

const mockSession: Session = {
  user: {
    name: "Story Admin",
    email: "admin@example.com",
    roles: ["admin"],
  },
  expires: "",
};

const meta: Meta<typeof TaskDetailsDrawer> = {
  title: "Features/Inbox/TaskDetailsDrawer",
  component: TaskDetailsDrawer,
  args: {
    task: mockTask,
    isOpen: true,
    canUndo: true,
    isActionPending: false,
    lastActionLabel: "Apply decision",
  },
  decorators: [
    (StoryComponent) => (
      <SessionProvider session={mockSession}>
        <StoryComponent />
      </SessionProvider>
    ),
  ],
};

export default meta;

type Story = StoryObj<typeof TaskDetailsDrawer>;

export const Default: Story = {
  args: {
    onApply: () => undefined,
    onDecline: () => undefined,
    onSnooze: () => undefined,
    onUndo: () => undefined,
    onClose: () => undefined,
  },
};
