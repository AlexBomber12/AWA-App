"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { ErrorState } from "@/components/data";
import { PageBody, PageHeader } from "@/components/layout";
import {
  type DecisionRulesResponse,
  type Rule,
  type SimulationScenario,
  type SimulationScenariosResponse,
  decisionRulesQueryKey,
  simulationScenariosQueryKey,
  useDecisionRulesQuery,
  useRunSimulationMutation,
  useSimulationScenariosQuery,
} from "@/lib/api/decisionClient";
import { usePermissions } from "@/lib/permissions";

import { useActionFlow } from "@/components/hooks/useActionFlow";
import { useToast } from "@/components/providers/ToastProvider";

import { DecisionRulesList } from "./DecisionRulesList";
import { SimulationPanel } from "./SimulationPanel";

const EMPTY_RULES: Rule[] = [];
const EMPTY_SCENARIOS: SimulationScenario[] = [];

export function DecisionEnginePage() {
  const rulesQuery = useDecisionRulesQuery();
  const scenariosQuery = useSimulationScenariosQuery();
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [togglingRuleId, setTogglingRuleId] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const toggleFlow = useActionFlow();
  const { pushToast } = useToast();
  const { can } = usePermissions();
  const canConfigure = can({ resource: "decision", action: "configure" });

  const rules = useMemo(() => rulesQuery.data?.rules ?? EMPTY_RULES, [rulesQuery.data]);
  const scenarios = useMemo(() => scenariosQuery.data?.scenarios ?? EMPTY_SCENARIOS, [scenariosQuery.data]);

  useEffect(() => {
    if (!selectedRuleId && rules.length > 0) {
      setSelectedRuleId(rules[0].id);
    }
  }, [rules, selectedRuleId]);

  useEffect(() => {
    if (!selectedScenarioId && selectedRuleId) {
      const match = scenarios.find((scenario) => scenario.ruleId === selectedRuleId);
      if (match) {
        setSelectedScenarioId(match.id);
      }
    }
  }, [selectedScenarioId, selectedRuleId, scenarios]);

  const selectedRule = useMemo(() => rules.find((rule) => rule.id === selectedRuleId) ?? null, [rules, selectedRuleId]);

  const updateRulesCache = useCallback(
    (ruleId: string, nextActive: boolean) => {
      const current = queryClient.getQueryData<DecisionRulesResponse>(decisionRulesQueryKey);
      if (!current) {
        return undefined;
      }
      const snapshot: DecisionRulesResponse = {
        ...current,
        rules: current.rules.map((rule) => ({ ...rule })),
      };
      const nextRules = current.rules.map((rule) =>
        rule.id === ruleId ? { ...rule, active: nextActive, updatedAt: new Date().toISOString() } : rule
      );
      queryClient.setQueryData(decisionRulesQueryKey, { ...current, rules: nextRules });
      return () => queryClient.setQueryData(decisionRulesQueryKey, snapshot);
    },
    [queryClient]
  );

  const appendScenario = useCallback(
    (scenario: SimulationScenario) => {
      queryClient.setQueryData<SimulationScenariosResponse>(simulationScenariosQueryKey, (current) => {
        if (!current) {
          return { scenarios: [scenario] };
        }
        const filtered = current.scenarios.filter((item) => item.id !== scenario.id);
        return { scenarios: [scenario, ...filtered] };
      });
    },
    [queryClient]
  );

  const handleToggleRule = useCallback(
    (rule: Rule, nextActive: boolean) => {
      setTogglingRuleId(rule.id);
      toggleFlow
        .runAction({
          id: `rule-${rule.id}`,
          label: nextActive ? "Activate rule" : "Pause rule",
          successMessage: nextActive ? `${rule.name} activated` : `${rule.name} paused`,
          errorMessage: `Unable to update ${rule.name}`,
          optimisticUpdate: () => updateRulesCache(rule.id, nextActive),
        })
        .catch(() => undefined)
        .finally(() => setTogglingRuleId(null));
    },
    [toggleFlow, updateRulesCache]
  );

  const runSimulationMutation = useRunSimulationMutation({
    onSuccess: (scenario) => {
      appendScenario(scenario);
      setSelectedScenarioId(scenario.id);
      pushToast({ title: "Simulation completed", variant: "success" });
    },
    onError: (error) => {
      pushToast({ title: error.message ?? "Unable to run simulation", variant: "error" });
    },
  });

  const handleRunSimulation = useCallback(
    (payload: { ruleId: string; input: Record<string, unknown> }) => {
      runSimulationMutation.mutate(payload);
    },
    [runSimulationMutation]
  );

  const handleSelectRule = (ruleId: string) => {
    setSelectedRuleId(ruleId);
    setSelectedScenarioId(null);
  };

  const handleSelectScenario = (scenarioId: string) => {
    setSelectedScenarioId(scenarioId);
  };

  return (
    <>
      <PageHeader
        title="Decision Engine"
        description="Review active rules, toggle their state, and run sandboxed simulations."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Decision Engine", active: true },
        ]}
      />
      <PageBody>
        <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
          <div>
            {rulesQuery.error ? (
              <ErrorState title="Unable to load rules" error={rulesQuery.error} onRetry={() => rulesQuery.refetch()} />
            ) : (
              <DecisionRulesList
                rules={rules}
                isLoading={rulesQuery.isPending || rulesQuery.isFetching}
                selectedRuleId={selectedRuleId}
                onSelectRule={handleSelectRule}
                onToggleRule={handleToggleRule}
                canConfigure={canConfigure}
                togglingRuleId={togglingRuleId}
                isMutatingRule={toggleFlow.isRunning}
              />
            )}
          </div>
          <div className="space-y-4">
            {scenariosQuery.error ? (
              <ErrorState
                title="Unable to load simulations"
                error={scenariosQuery.error}
                onRetry={() => scenariosQuery.refetch()}
              />
            ) : null}
            <SimulationPanel
              selectedRule={selectedRule}
              scenarios={scenarios}
              isLoading={scenariosQuery.isPending || scenariosQuery.isFetching}
              onRunSimulation={handleRunSimulation}
              isRunningSimulation={runSimulationMutation.isPending}
              selectedScenarioId={selectedScenarioId}
              onSelectScenario={handleSelectScenario}
              canConfigure={canConfigure}
            />
          </div>
        </div>
      </PageBody>
    </>
  );
}
