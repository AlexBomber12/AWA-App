import type { Meta, StoryObj } from "@storybook/react";
import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";

import { TaskDetailsDrawer } from "@/components/features/inbox/TaskDetailsDrawer";
import type { Task } from "@/lib/api/inboxClient";

const mockTask: Task = {
  id: "drawer-task",
  source: "decision_engine",
  entity: { type: "sku", id: "SKU-777", asin: "B00DRAWER", label: "Story Drawer SKU" },
  summary: "Review price adjustment for Story Drawer SKU",
  assignee: "Story Admin",
  due: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
  state: "open",
  decision: {
    decision: "request_price",
    priority: "high",
    deadlineAt: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
    defaultAction: "Email vendor for refreshed quote",
    why: ["ROI dipped to 13%", "Competitor inventory spike"],
    alternatives: ["Wait until ingestion", "Switch vendor"],
    nextRequestAt: new Date(Date.now() + 48 * 60 * 60 * 1000).toISOString(),
  },
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
