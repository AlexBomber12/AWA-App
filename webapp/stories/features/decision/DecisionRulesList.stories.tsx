import type { Meta, StoryObj } from "@storybook/react";

import { DecisionRulesList } from "@/components/features/decision/DecisionRulesList";
import type { Rule } from "@/lib/api/decisionClient";

const MOCK_RULES: Rule[] = [
  {
    id: "rule-story-1",
    name: "Story ROI Guardrail",
    description: "Keeps ROI above 20%.",
    isActive: true,
    enabled: true,
    scope: "sku",
    conditions: [{ field: "roi", op: "<", value: 20 }],
    actions: [{ action: "request_discount", defaultAction: "Request 3% discount" }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "rule-story-2",
    name: "Story Vendor Drift",
    description: "Flags vendors exceeding target lead time.",
    isActive: false,
    enabled: false,
    scope: "vendor",
    conditions: [{ field: "lead_time_slip", op: ">", value: 2 }],
    actions: [{ action: "blocked_observe", defaultAction: "Pause repricing" }],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

const meta: Meta<typeof DecisionRulesList> = {
  title: "Features/Decision/DecisionRulesList",
  component: DecisionRulesList,
  args: {
    rules: MOCK_RULES,
    isLoading: false,
    onSelectRule: () => undefined,
  },
};

export default meta;

type Story = StoryObj<typeof DecisionRulesList>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    rules: [],
    isLoading: true,
  },
};
