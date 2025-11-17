import type { Meta, StoryObj } from "@storybook/react";

import { PageBody, PageHeader } from "@/components/layout";
import { Button } from "@/components/ui";

const meta: Meta<typeof PageHeader> = {
  title: "Layout/Page Primitives",
  component: PageHeader,
  args: {
    title: "Feature workspace",
    description: "Standardized header + body containers for feature slices.",
  },
  render: (args) => (
    <>
      <PageHeader {...args} />
      <PageBody>
        <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
          <p className="text-muted-foreground">
            Use PageBody to wrap cards, forms, and tables so consistent padding is applied.
          </p>
        </div>
      </PageBody>
    </>
  ),
};

export default meta;
type Story = StoryObj<typeof PageHeader>;

export const Basic: Story = {};

export const WithActions: Story = {
  args: {
    actions: (
      <Button size="sm" variant="outline">
        Secondary action
      </Button>
    ),
    breadcrumbs: [
      { label: "Dashboard", href: "/dashboard" },
      { label: "Feature", active: true },
    ],
  },
};
