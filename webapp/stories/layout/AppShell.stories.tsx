import type { Meta, StoryObj } from "@storybook/react";
import type { Session } from "next-auth";

import { AppShell, PageBody, PageHeader } from "@/components/layout";

const mockSession = {
  user: {
    name: "Ops Lead",
    email: "ops@example.com",
    roles: ["admin"],
  },
  expires: "",
  accessToken: "demo-token",
} as Session & { accessToken: string };

const meta: Meta<typeof AppShell> = {
  title: "Layout/AppShell",
  component: AppShell,
  args: {
    initialSession: mockSession,
    initialPath: "/dashboard",
    children: (
      <>
        <PageHeader title="Storybook dashboard" description="Visual check for AppShell layout." />
        <PageBody>
          <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
            <p className="text-muted-foreground">
              Use this story to validate responsive shell styles, navigation highlighting, and
              context providers.
            </p>
          </div>
        </PageBody>
      </>
    ),
  },
};

export default meta;
type Story = StoryObj<typeof AppShell>;

export const Default: Story = {};
