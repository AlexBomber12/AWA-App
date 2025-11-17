"use client";

import { useMemo, useState } from "react";

import type { Rule, SimulationScenario } from "@/lib/api/decisionClient";
import { PermissionGuard } from "@/lib/permissions";
import { cn } from "@/lib/utils";

import { Button, Input } from "@/components/ui";

type SimulationPanelProps = {
  selectedRule: Rule | null;
  scenarios: SimulationScenario[];
  isLoading?: boolean;
  onRunSimulation: (payload: { ruleId: string; input: Record<string, unknown> }) => void;
  isRunningSimulation?: boolean;
  selectedScenarioId: string | null;
  onSelectScenario: (scenarioId: string) => void;
  canConfigure?: boolean;
};

const formatScenarioStatus = (scenario: SimulationScenario) => (scenario.result ? "Completed" : "Pending");

const formatStatLabel = (label: string) =>
  label
    .replace(/([A-Z])/g, " $1")
    .replace(/_/g, " ")
    .trim();

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
  const [roiDelta, setRoiDelta] = useState("3.5");
  const [priceChange, setPriceChange] = useState("1.2");
  const [notes, setNotes] = useState("");

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
        roiDelta: Number(roiDelta) || 0,
        priceChange: Number(priceChange) || 0,
        notes: notes.trim() || undefined,
      },
    };
    onRunSimulation(payload);
  };

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
            ROI delta %
            <Input value={roiDelta} onChange={(event) => setRoiDelta(event.target.value)} className="mt-1" />
          </label>
          <label className="text-sm font-medium">
            Price change %
            <Input value={priceChange} onChange={(event) => setPriceChange(event.target.value)} className="mt-1" />
          </label>
        </div>
        <label className="text-sm font-medium">
          Notes
          <textarea
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-transparent p-2 text-sm"
            rows={3}
            placeholder="Optional context for the scenario"
          />
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
                  <p className="text-xs text-muted-foreground">{formatScenarioStatus(scenario)}</p>
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
        ) : activeScenario.result ? (
          <div className="mt-4 space-y-4">
            <div>
              <p className="text-base font-semibold">{activeScenario.result.summary}</p>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {Object.entries(activeScenario.result.stats).map(([key, value]) => (
                  <div key={key} className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                    <p className="text-xs uppercase text-muted-foreground">{formatStatLabel(key)}</p>
                    <p className="text-lg font-semibold">{value}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Sample decisions</p>
              <div className="space-y-3">
                {activeScenario.result.sampleDecisions.map((decision, index) => (
                  <div key={`${decision.decision}-${index}`} className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
                    <p className="font-semibold capitalize">{formatDecisionLabel(decision.decision)}</p>
                    <p className="text-xs text-muted-foreground">Priority: {decision.priority}</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-xs text-muted-foreground">
                      {decision.why.map((reason) => (
                        <li key={reason}>{reason}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-muted-foreground">
            Simulation is pending. Once the result is available it will appear here.
          </p>
        )}
      </div>
    </div>
  );
}
