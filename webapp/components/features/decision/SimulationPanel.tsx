"use client";

import { useMemo, useState } from "react";

import type { Rule, SimulationInput, SimulationScenario } from "@/lib/api/decisionClient";
import { PermissionGuard } from "@/lib/permissions/client";
import { cn } from "@/lib/utils";

import { Button, Checkbox, Input } from "@/components/ui";
import { formatTaskPriority } from "../inbox/taskFormatters";

type SimulationPanelProps = {
  selectedRule: Rule | null;
  scenarios: SimulationScenario[];
  isLoading?: boolean;
  onRunSimulation: (payload: { ruleId: string; input: SimulationInput }) => void;
  isRunningSimulation?: boolean;
  selectedScenarioId: string | null;
  onSelectScenario: (scenarioId: string) => void;
  canConfigure?: boolean;
};

const formatDecisionLabel = (value: string) => value.replaceAll("_", " ");

export function SimulationPanel({
  selectedRule,
  scenarios,
  isLoading,
  onRunSimulation,
  isRunningSimulation,
  selectedScenarioId,
  onSelectScenario,
  canConfigure = false,
}: SimulationPanelProps) {
  const [price, setPrice] = useState("24.5");
  const [cost, setCost] = useState("13.2");
  const [category, setCategory] = useState("");
  const [volatility, setVolatility] = useState("5");
  const [observeOnly, setObserveOnly] = useState(false);

  const filteredScenarios = useMemo(
    () => scenarios.filter((scenario) => !selectedRule || scenario.ruleId === selectedRule.id),
    [scenarios, selectedRule]
  );

  const activeScenario = filteredScenarios.find((scenario) => scenario.id === selectedScenarioId) ?? filteredScenarios[0] ?? null;

  if (!selectedRule) {
    return (
      <div className="rounded-2xl border border-dashed border-border bg-muted/20 p-6 text-sm text-muted-foreground">
        Select a rule to inspect recent simulations.
      </div>
    );
  }

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = (event) => {
    event.preventDefault();
    if (!selectedRule || !canConfigure) {
      return;
    }

    const payload = {
      ruleId: selectedRule.id,
      input: {
        price: Number(price) || undefined,
        cost: Number(cost) || undefined,
        volatility: Number(volatility) || undefined,
        category: category.trim() || undefined,
        observeOnly,
      },
    };
    onRunSimulation(payload);
  };

  const activeMetrics =
    activeScenario?.result ?? (activeScenario as { metrics?: SimulationScenario["result"] } | null)?.metrics;

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-border bg-background p-5 shadow-sm">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Simulation input</p>
          <p className="text-lg font-semibold">{selectedRule.name}</p>
          <p className="text-sm text-muted-foreground">{selectedRule.description ?? "No description provided."}</p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="text-sm font-medium">
            Target price
            <Input value={price} onChange={(event) => setPrice(event.target.value)} className="mt-1" />
          </label>
          <label className="text-sm font-medium">
            Cost
            <Input value={cost} onChange={(event) => setCost(event.target.value)} className="mt-1" />
          </label>
          <label className="text-sm font-medium">
            Volatility %
            <Input value={volatility} onChange={(event) => setVolatility(event.target.value)} className="mt-1" />
          </label>
          <label className="text-sm font-medium">
            Category
            <Input value={category} onChange={(event) => setCategory(event.target.value)} className="mt-1" placeholder="Optional category" />
          </label>
        </div>
        <label className="flex items-center gap-2 text-sm font-medium">
          <Checkbox checked={observeOnly} onChange={(event) => setObserveOnly(event.target.checked)} />
          Observe only (no actions saved)
        </label>
        <PermissionGuard
          resource="decision"
          action="configure"
          fallback={
            <p className="rounded-md border border-border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
              You can view rules but cannot run simulations.
            </p>
          }
        >
          <Button type="submit" isLoading={isRunningSimulation} disabled={!canConfigure}>
            Run simulation
          </Button>
        </PermissionGuard>
      </form>

      <div className="rounded-2xl border border-border bg-background p-5 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Previous simulations</p>
        {isLoading ? (
          <div className="mt-4 space-y-2">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={`scenario-skeleton-${index}`} className="h-12 animate-pulse rounded-lg bg-muted/40" />
            ))}
          </div>
        ) : filteredScenarios.length === 0 ? (
          <p className="mt-4 text-sm text-muted-foreground">No simulations recorded for this rule yet.</p>
        ) : (
          <div className="mt-4 space-y-2">
            {filteredScenarios.map((scenario) => {
              const metrics = scenario.result ?? (scenario as { metrics?: SimulationScenario["result"] }).metrics;
              const isSelected = scenario.id === activeScenario?.id;
              return (
                <button
                  key={scenario.id}
                  type="button"
                  onClick={() => onSelectScenario(scenario.id)}
                  className={cn(
                    "w-full rounded-lg border px-3 py-2 text-left transition-colors",
                    isSelected ? "border-brand bg-brand/5" : "border-border hover:bg-muted/30"
                  )}
                >
                  <p className="text-sm font-semibold">{scenario.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {metrics ? "Simulation only, not saved" : "Pending"}
                  </p>
                </button>
              );
            })}
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-border bg-background p-5 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Scenario result</p>
        {!activeScenario ? (
          <p className="mt-4 text-sm text-muted-foreground">Select a simulation to view details.</p>
        ) : !activeMetrics ? (
          <p className="mt-4 text-sm text-muted-foreground">
            Simulation is pending. Once the result is available it will appear here.
          </p>
        ) : (
          <div className="mt-4 space-y-4">
            <div>
              <p className="text-base font-semibold">{activeScenario.description ?? "Simulation output"}</p>
              <p className="text-xs text-muted-foreground">Simulation only, not saved.</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {activeMetrics.roi !== undefined ? (
                  <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                    <p className="text-xs uppercase text-muted-foreground">ROI</p>
                    <p className="text-lg font-semibold">{activeMetrics.roi.toFixed(1)}%</p>
                  </div>
                ) : null}
                {activeMetrics.riskAdjustedRoi !== undefined ? (
                  <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                    <p className="text-xs uppercase text-muted-foreground">Risk-adjusted ROI</p>
                    <p className="text-lg font-semibold">{activeMetrics.riskAdjustedRoi.toFixed(1)}%</p>
                  </div>
                ) : null}
                {activeMetrics.maxCogs !== undefined ? (
                  <div className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                    <p className="text-xs uppercase text-muted-foreground">Max COGS</p>
                    <p className="text-lg font-semibold">${activeMetrics.maxCogs.toFixed(2)}</p>
                  </div>
                ) : null}
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Simulated decisions</p>
              <div className="space-y-3">
                {(activeScenario.decisions ?? []).map((decision, index) => (
                  <div key={`${decision.decision}-${index}`} className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                    <p className="font-semibold capitalize">{formatDecisionLabel(decision.decision)}</p>
                    <p className="text-xs text-muted-foreground">Priority: {formatTaskPriority(decision.priority)}</p>
                    <div className="mt-2 space-y-1 text-xs text-muted-foreground">
                      {decision.metrics?.roi !== undefined ? <p>ROI: {decision.metrics.roi.toFixed(1)}%</p> : null}
                      {decision.metrics?.riskAdjustedRoi !== undefined ? (
                        <p>Risk-adjusted ROI: {decision.metrics.riskAdjustedRoi.toFixed(1)}%</p>
                      ) : null}
                    </div>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                      {decision.why.map((reason, index) => {
                        const label = typeof reason === "string" ? reason : reason.title;
                        return <li key={`${label}-${index}`}>{label}</li>;
                      })}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
