import type { Meta, StoryObj } from "@storybook/react";

import { DecisionRulesList } from "@/components/features/decision/DecisionRulesList";
import type { Rule } from "@/lib/api/decisionClient";

const MOCK_RULES: Rule[] = [
  {
    id: "rule-story-1",
    name: "Story ROI Guardrail",
    description: "Keeps ROI above 20%.",
    active: true,
    scope: "sku",
    params: { roiMin: 20 },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: "rule-story-2",
    name: "Story Vendor Drift",
    description: "Flags vendors exceeding target lead time.",
    active: false,
    scope: "vendor",
    params: { toleranceDays: 2 },
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
    canConfigure: true,
    onSelectRule: () => undefined,
    onToggleRule: () => undefined,
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
