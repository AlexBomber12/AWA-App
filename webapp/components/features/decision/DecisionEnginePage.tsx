"use client";

import { useEffect, useMemo, useState } from "react";

import { useQueryClient } from "@tanstack/react-query";

import { ErrorState, FilterBar } from "@/components/data";
import { PageBody, PageHeader } from "@/components/layout";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";
import {
  decisionSummaryQueryKey,
  useDecisionSummaryQuery,
  useRunSimulationMutation,
} from "@/lib/api/decisionClient";
import type { Rule, SimulationInput, SimulationScenario } from "@/lib/api/decisionClient";
import { PermissionGuard, usePermissions } from "@/lib/permissions/client";

import { useToast } from "@/components/providers/ToastProvider";

import { DecisionRulesList } from "./DecisionRulesList";
import { SimulationPanel } from "./SimulationPanel";

type RuleFilters = {
  status: "all" | "active" | "inactive";
  scope: "all" | Rule["scope"];
};

const DEFAULT_RULE_FILTERS: RuleFilters = {
  status: "all",
  scope: "all",
};

export function DecisionEnginePage() {
  const decisionQuery = useDecisionSummaryQuery();
  const [selectedRuleId, setSelectedRuleId] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [ruleFilters, setRuleFilters] = useState<RuleFilters>(DEFAULT_RULE_FILTERS);
  const queryClient = useQueryClient();
  const { pushToast } = useToast();
  const { can } = usePermissions();
  const canConfigure = can({ resource: "decision", action: "configure" });

  const rules = useMemo(() => decisionQuery.data?.rules ?? [], [decisionQuery.data]);
  const filteredRules = useMemo(() => {
    return rules.filter((rule) => {
      const active = "enabled" in rule ? rule.enabled : (rule as { isActive?: boolean }).isActive;
      const matchesStatus =
        ruleFilters.status === "all" ? true : ruleFilters.status === "active" ? active : !active;
      const matchesScope = ruleFilters.scope === "all" ? true : rule.scope === ruleFilters.scope;
      return matchesStatus && matchesScope;
    });
  }, [ruleFilters, rules]);

  const scenarios = useMemo(() => decisionQuery.data?.scenarios ?? [], [decisionQuery.data]);

  useEffect(() => {
    if (!selectedRuleId && filteredRules.length > 0) {
      setSelectedRuleId(filteredRules[0].id);
    }
  }, [filteredRules, selectedRuleId]);

  useEffect(() => {
    if (!selectedScenarioId && selectedRuleId) {
      const match = scenarios.find((scenario) => scenario.ruleId === selectedRuleId);
      if (match) {
        setSelectedScenarioId(match.id);
      }
    }
  }, [selectedScenarioId, selectedRuleId, scenarios]);

  const selectedRule = useMemo(() => rules.find((rule) => rule.id === selectedRuleId) ?? null, [rules, selectedRuleId]);

  const runSimulationMutation = useRunSimulationMutation({
    onSuccess: (scenario) => {
      queryClient.setQueryData(decisionSummaryQueryKey, (current: unknown) => {
        const summary = current as { rules?: Rule[]; scenarios?: SimulationScenario[]; tasks?: unknown };
        const existingScenarios = summary?.scenarios ?? [];
        const filtered = existingScenarios.filter((item) => item.id !== scenario.id);
        return {
          rules: summary?.rules ?? rules,
          scenarios: [scenario, ...filtered],
          tasks: summary?.tasks,
        };
      });
      setSelectedScenarioId(scenario.id);
      pushToast({ title: "Simulation completed", variant: "success" });
    },
    onError: (error) => {
      pushToast({ title: error.message ?? "Unable to run simulation", variant: "error" });
    },
  });

  const handleRunSimulation = (payload: { ruleId: string; input: SimulationInput }) => {
    runSimulationMutation.mutate(payload);
  };

  const handleSelectRule = (ruleId: string) => {
    setSelectedRuleId(ruleId);
    setSelectedScenarioId(null);
  };

  const handleSelectScenario = (scenarioId: string) => {
    setSelectedScenarioId(scenarioId);
  };

  const unauthorized = (
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
        <div className="rounded-2xl border border-border bg-muted/30 p-8 text-center">
          <p className="text-base font-semibold">Not authorized</p>
          <p className="mt-1 text-sm text-muted-foreground">You need admin access to view Decision Engine rules.</p>
        </div>
      </PageBody>
    </>
  );

  return (
    <PermissionGuard resource="decision" action="view" requiredRoles={["admin"]} fallback={unauthorized}>
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
        <FilterBar
          isDirty={
            ruleFilters.status !== DEFAULT_RULE_FILTERS.status || ruleFilters.scope !== DEFAULT_RULE_FILTERS.scope
          }
          onReset={() => setRuleFilters(DEFAULT_RULE_FILTERS)}
          disableActions={decisionQuery.isFetching}
        >
          <div className="flex flex-col gap-1 text-sm">
            <span className="font-semibold">Status</span>
            <Select
              value={ruleFilters.status}
              onValueChange={(value) =>
                setRuleFilters((current) => ({ ...current, status: value as RuleFilters["status"] }))
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Disabled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-1 text-sm">
            <span className="font-semibold">Scope</span>
            <Select
              value={ruleFilters.scope}
              onValueChange={(value) =>
                setRuleFilters((current) => ({ ...current, scope: value as RuleFilters["scope"] }))
              }
            >
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Scope" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="category">Category</SelectItem>
                <SelectItem value="vendor">Vendor</SelectItem>
                <SelectItem value="sku">SKU</SelectItem>
                <SelectItem value="campaign">Campaign</SelectItem>
                <SelectItem value="global">Global</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </FilterBar>
        <div className="grid gap-6 lg:grid-cols-[320px,1fr]">
          <div>
            {decisionQuery.error ? (
              <ErrorState title="Unable to load rules" error={decisionQuery.error} onRetry={() => decisionQuery.refetch()} />
            ) : (
              <DecisionRulesList
                rules={filteredRules}
                isLoading={decisionQuery.isPending || decisionQuery.isFetching}
                selectedRuleId={selectedRuleId}
                onSelectRule={handleSelectRule}
              />
            )}
          </div>
          <div className="space-y-4">
            {decisionQuery.error ? (
              <ErrorState
                title="Unable to load simulations"
                error={decisionQuery.error}
                onRetry={() => decisionQuery.refetch()}
              />
            ) : null}
            <SimulationPanel
              selectedRule={selectedRule}
              scenarios={scenarios}
              isLoading={decisionQuery.isPending || decisionQuery.isFetching}
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
    </PermissionGuard>
  );
}
