import type { Meta, StoryObj } from "@storybook/react";
import { SessionProvider } from "next-auth/react";
import type { Session } from "next-auth";

import { SimulationPanel } from "@/components/features/decision/SimulationPanel";
import type { Rule, SimulationScenario } from "@/lib/api/decisionClient";

const mockRule: Rule = {
  id: "rule-story",
  name: "Story Simulation Rule",
  description: "Demonstrates the simulation panel.",
  active: true,
  scope: "global",
  params: {},
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
};

const mockScenarios: SimulationScenario[] = [
  {
    id: "scenario-a",
    name: "Scenario A",
    description: "First mock scenario",
    ruleId: "rule-story",
    input: { roiDelta: 4 },
    result: {
      summary: "Projected +4% ROI uplift across 80 SKUs.",
      stats: {
        affectedSkus: 80,
        avgRoiDelta: 4,
      },
      sampleDecisions: [
        {
          decision: "update_price",
          priority: "high",
          defaultAction: "Increase price by 1%",
          why: ["ROI under guardrail"],
          alternatives: ["Request discount"],
        },
      ],
    },
  },
  {
    id: "scenario-b",
    name: "Scenario B",
    description: "Pending scenario",
    ruleId: "rule-story",
    input: { roiDelta: 2 },
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
