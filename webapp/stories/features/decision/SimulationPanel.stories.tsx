import type { Meta, StoryObj } from "@storybook/react";
import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";

import { SimulationPanel } from "@/components/features/decision/SimulationPanel";
import type { Rule, SimulationScenario } from "@/lib/api/decisionClient";

const mockRule: Rule = {
  id: "rule-story",
  name: "Story Simulation Rule",
  description: "Demonstrates the simulation panel.",
  isActive: true,
  enabled: true,
  scope: "global",
  conditions: [{ field: "roi", op: "<", value: 18 }],
  actions: [{ action: "update_price" }],
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

const mockScenarios: SimulationScenario[] = [
  {
    id: "scenario-a",
    name: "Scenario A",
    description: "First mock scenario",
    ruleId: "rule-story",
    baselineSku: "scenario-a",
    parameters: { price: 23, cost: 12.4 },
    result: {
      roi: 18.2,
      margin: 12.2,
      riskAdjustedRoi: 15.4,
      maxCogs: 14.2,
    },
    metrics: {
      roi: 18.2,
      margin: 12.2,
      riskAdjustedRoi: 15.4,
      maxCogs: 14.2,
    },
    decisions: [
      {
        decision: "update_price",
        priority: "high",
        defaultAction: "Increase price by 1%",
        why: ["ROI under guardrail"],
        alternatives: [{ decision: "request_discount", label: "Request discount" }],
      },
    ],
    createdAt: new Date().toISOString(),
  },
  {
    id: "scenario-b",
    name: "Scenario B",
    description: "Pending scenario",
    ruleId: "rule-story",
    baselineSku: "scenario-b",
    parameters: { price: 21, cost: 11.5 },
    result: { roi: 0, margin: 0 },
    decisions: [],
    createdAt: new Date().toISOString(),
  },
];

const mockSession: Session = {
  user: {
    name: "Story Admin",
    email: "admin@example.com",
    roles: ["admin"],
  },
  expires: "",
};

const meta: Meta<typeof SimulationPanel> = {
  title: "Features/Decision/SimulationPanel",
  component: SimulationPanel,
  args: {
    selectedRule: mockRule,
    scenarios: mockScenarios,
    selectedScenarioId: "scenario-a",
    onRunSimulation: () => undefined,
    onSelectScenario: () => undefined,
    canConfigure: true,
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

type Story = StoryObj<typeof SimulationPanel>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    scenarios: [],
    isLoading: true,
  },
};
