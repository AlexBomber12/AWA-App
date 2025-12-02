import type { Meta, StoryObj } from "@storybook/react";
import { expect, userEvent, waitFor, within } from "@storybook/test";
import type { Session } from "next-auth";

import { DecisionEnginePage } from "@/components/features/decision/DecisionEnginePage";
import { AppShell } from "@/components/layout";
import type { DecisionRulesResponse, SimulationScenariosResponse } from "@/lib/api/decisionClient";
import type { SimulationScenario } from "@/lib/api/bffTypes";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

const mockSession = {
  user: {
    name: "Admin",
    email: "admin@example.com",
    roles: ["admin"],
  },
  expires: "",
  accessToken: "storybook-token",
} as Session & { accessToken: string };

const rulesResponse: DecisionRulesResponse = {
  rules: [
    {
      id: "rule-story-guardrail",
      name: "Story Guardrail",
      description: "Ensures ROI stays above 15%.",
      isActive: true,
      enabled: true,
      scope: "category",
      conditions: [{ field: "roi", op: "<", value: 15, category: "Home" }],
      actions: [{ action: "request_discount", defaultAction: "Request 5% discount" }],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: "rule-story-vendor",
      name: "Story Vendor Lead Time",
      description: "Blocks repricing when lead times slip.",
      isActive: false,
      enabled: false,
      scope: "vendor",
      conditions: [{ field: "lead_time_slip", op: ">", value: 2 }],
      actions: [{ action: "blocked_observe", defaultAction: "Pause repricing" }],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ],
};

const scenariosResponse: SimulationScenariosResponse = {
  scenarios: [
    {
      id: "scenario-story-1",
      name: "Story ROI boost",
      description: "Applies guardrail to promo batch.",
      ruleId: "rule-story-guardrail",
      baselineSku: "story-sku-1",
      parameters: { price: 23, cost: 12.8 },
      result: { roi: 18.4, margin: 11.2, riskAdjustedRoi: 15.9, maxCogs: 14.1 },
      metrics: { roi: 18.4, margin: 11.2, riskAdjustedRoi: 15.9, maxCogs: 14.1 },
      decisions: [
        {
          decision: "update_price",
          priority: "high",
          defaultAction: "Increase price by 1%",
          why: ["ROI below 15%"],
          alternatives: [{ decision: "request_discount", label: "Request discount" }],
        },
      ],
      createdAt: new Date().toISOString(),
    },
  ],
};

const newScenario: SimulationScenario = {
  id: "scenario-story-new",
  name: "Story Simulation",
  description: "New simulation",
  ruleId: "rule-story-guardrail",
  baselineSku: "story-sku-1",
  parameters: { price: 22.4, cost: 11.5 },
  result: { roi: 20.1, margin: 12.8, riskAdjustedRoi: 18.4, maxCogs: 13.8 },
  decisions: [
    {
      decision: "update_price",
      priority: "high",
      defaultAction: "Apply +1% price",
      why: ["Projected ROI gain"],
      alternatives: [{ decision: "wait_until", label: "Observe for 24h" }],
    },
  ],
  createdAt: new Date().toISOString(),
};

type DecisionStoryMode = "default" | "loading" | "error";

const delayedResponse = (response: Response, delayMs = 1500) =>
  new Promise<Response>((resolve) => setTimeout(() => resolve(response), delayMs));

const buildHandlers = (mode: DecisionStoryMode): FetchMockHandler[] => [
  {
    predicate: ({ url, method }) => method === "GET" && url.includes("/api/bff/decision"),
    response: ({ url }) => {
      if (mode === "error") {
        return new Response(JSON.stringify({ code: "BFF_ERROR", message: "Bad request" }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        });
      }
      const resource = new URL(url).searchParams.get("resource");
      const payload =
        resource === "rules"
          ? rulesResponse
          : resource === "scenarios"
            ? scenariosResponse
            : { rules: rulesResponse.rules, scenarios: scenariosResponse.scenarios };
      const response = new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
      return mode === "loading" ? delayedResponse(response) : response;
    },
  },
  {
    predicate: ({ url, method }) => method === "POST" && url.includes("/api/bff/decision"),
    response: () =>
      new Response(JSON.stringify(newScenario), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
  },
];

const meta: Meta<typeof DecisionEnginePage> = {
  title: "Features/Decision/DecisionEnginePage",
  component: DecisionEnginePage,
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof DecisionEnginePage>;

export const Default: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("default")}>
      <AppShell initialSession={mockSession} initialPath="/decision">
        <DecisionEnginePage />
      </AppShell>
    </FetchMock>
  ),
};

export const LoadingState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("loading")}>
      <AppShell initialSession={mockSession} initialPath="/decision">
        <DecisionEnginePage />
      </AppShell>
    </FetchMock>
  ),
};

export const ErrorState: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("error")}>
      <AppShell initialSession={mockSession} initialPath="/decision">
        <DecisionEnginePage />
      </AppShell>
    </FetchMock>
  ),
};

export const RunSimulation: Story = {
  render: () => (
    <FetchMock handlers={buildHandlers("default")}>
      <AppShell initialSession={mockSession} initialPath="/decision">
        <DecisionEnginePage />
      </AppShell>
    </FetchMock>
  ),
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const storyUser = userEvent.setup();
    await waitFor(() => expect(canvas.getByText("Story Guardrail")).toBeInTheDocument());
    await storyUser.click(canvas.getByRole("button", { name: /Run simulation/i }));
    await waitFor(() => expect(canvas.getByText("Story Simulation")).toBeInTheDocument());
  },
};
