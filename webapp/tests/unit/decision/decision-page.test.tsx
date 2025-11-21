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
import type { DecisionRulesResponse, SimulationScenariosResponse } from "@/lib/api/decisionClient";
import type { SimulationScenario } from "@/lib/api/decisionTypes";

const user = userEvent.setup();

const rulesResponse: DecisionRulesResponse = {
  rules: [
    {
      id: "rule-1",
      name: "Story Rule 1",
      description: "First rule",
      isActive: true,
      scope: "sku",
      conditions: [{ field: "roi", operator: "<", value: 20 }],
      actions: [{ action: "update_price" }],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    },
    {
      id: "rule-2",
      name: "Story Rule 2",
      description: "Second rule",
      isActive: false,
      scope: "vendor",
      conditions: [{ vendorId: "22", field: "lead_time_slip", operator: ">", value: 2 }],
      actions: [{ action: "blocked_observe" }],
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
      metrics: { roi: 18.4, riskAdjustedRoi: 16.1, maxCogs: 14.5 },
      decisions: [
        {
          decision: "update_price",
          priority: "high",
          defaultAction: "Adjust price",
          why: ["ROI low"],
          alternatives: [{ decision: "request_discount", label: "Request discount" }],
        },
      ],
      createdAt: new Date().toISOString(),
    },
  ],
};

const newScenario: SimulationScenario = {
  id: "scenario-new",
  name: "Story Simulation",
  description: "New simulation",
  ruleId: "rule-1",
  input: { roiDelta: 4 },
  metrics: { roi: 21.2, riskAdjustedRoi: 19.1, maxCogs: 13.2 },
  decisions: [
    {
      decision: "update_price",
      priority: "high",
      defaultAction: "Boost price",
      why: ["Projected ROI gain"],
      alternatives: [{ decision: "continue", label: "Continue" }],
    },
  ],
  createdAt: new Date().toISOString(),
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
  rest.post("http://localhost:3000/api/bff/decision", (_req, res, ctx) => {
    return res(ctx.status(201), ctx.json(newScenario));
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
  it("renders rules and allows selecting a rule", async () => {
    renderWithProviders(<DecisionEnginePage />);

    const ruleCard = await screen.findByRole("button", { name: /Story Rule 1/i });
    expect(within(ruleCard).getByText(/Active/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Story Rule 2/i }));
    await waitFor(() => expect(screen.getAllByRole("button", { name: /Story Rule/i }).length).toBeGreaterThanOrEqual(2));
  });

  it("runs a simulation and displays the new result", async () => {
    renderWithProviders(<DecisionEnginePage />);

    await waitFor(() => expect(screen.getByText("Story Rule 1")).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: /Run simulation/i }));

    await waitFor(() => expect(screen.getByText("Story Simulation")).toBeInTheDocument());
    expect(screen.getAllByText(/Simulation only/).length).toBeGreaterThan(0);
  });
});
