import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { rest } from "msw";
import { setupServer } from "msw/node";
import type { Session } from "next-auth";
import { SessionProvider } from "next-auth/react";
import type { ReactNode } from "react";

import { DecisionEnginePage } from "@/components/features/decision/DecisionEnginePage";
import { ToastProvider } from "@/components/providers/ToastProvider";
import type { DecisionRulesResponse, SimulationScenario, SimulationScenariosResponse } from "@/lib/api/decisionClient";

const user = userEvent.setup();

const rulesResponse: DecisionRulesResponse = {
  rules: [
    {
      id: "rule-1",
      name: "Story Rule 1",
      description: "First rule",
      active: true,
      scope: "sku",
      params: {},
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: "rule-2",
      name: "Story Rule 2",
      description: "Second rule",
      active: false,
      scope: "vendor",
      params: {},
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
  ],
};

const scenariosResponse: SimulationScenariosResponse = {
  scenarios: [
    {
      id: "scenario-1",
      name: "Scenario One",
      description: "Completed scenario",
      ruleId: "rule-1",
      input: {},
      result: {
        summary: "Existing scenario summary",
        stats: { affectedSkus: 10, avgRoiDelta: 2 },
        sampleDecisions: [
          {
            decision: "update_price",
            priority: "high",
            defaultAction: "Adjust price",
            why: ["ROI low"],
            alternatives: ["Request discount"],
          },
        ],
      },
    },
  ],
};

const newScenario: SimulationScenario = {
  id: "scenario-new",
  name: "Story Simulation",
  description: "New simulation",
  ruleId: "rule-1",
  input: { roiDelta: 4 },
  result: {
    summary: "Simulation success output",
    stats: { affectedSkus: 25, avgRoiDelta: 4 },
    sampleDecisions: [
      {
        decision: "update_price",
        priority: "high",
        defaultAction: "Boost price",
        why: ["Projected ROI gain"],
        alternatives: ["Continue"],
      },
    ],
  },
};

const server = setupServer(
  rest.get("http://localhost:3000/api/bff/decision", (req, res, ctx) => {
    const resource = req.url.searchParams.get("resource");
    if (resource === "rules") {
      return res(ctx.json(rulesResponse));
    }
    if (resource === "scenarios") {
      return res(ctx.json(scenariosResponse));
    }
    return res(ctx.json({ rules: rulesResponse.rules, scenarios: scenariosResponse.scenarios }));
  }),
  rest.post("http://localhost:3000/api/bff/decision/simulate", (_req, res, ctx) => {
    return res(ctx.json(newScenario));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Admin",
    email: "admin@example.com",
    roles,
  },
  expires: "",
});

const renderWithProviders = (ui: ReactNode, roles: string[] = ["admin"]) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <SessionProvider session={buildSession(roles)}>
      <ToastProvider>
        <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
      </ToastProvider>
    </SessionProvider>
  );
};

describe("DecisionEnginePage", () => {
  it("renders rules and toggles active flag", async () => {
    renderWithProviders(<DecisionEnginePage />);

    const ruleCard = await screen.findByRole("button", { name: /Story Rule 1/i });
    const toggleButton = within(ruleCard).getByRole("button", { name: /^Pause$/i });
    await user.click(toggleButton);

    await waitFor(() => {
      expect(within(ruleCard).getByRole("button", { name: /^Activate$/i })).toBeInTheDocument();
    });
  });

  it("runs a simulation and displays the new result", async () => {
    renderWithProviders(<DecisionEnginePage />);

    await waitFor(() => expect(screen.getByText("Story Rule 1")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Run simulation/i }));

    await waitFor(() => expect(screen.getByText("Simulation success output")).toBeInTheDocument());
  });
});
