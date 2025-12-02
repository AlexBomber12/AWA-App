import type { UseMutationOptions } from "@tanstack/react-query";

import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiMutation } from "@/lib/api/useApiMutation";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";
import type { DecisionSummary, Rule, SimulationScenario } from "@/lib/api/bffTypes";
import type { DecisionPayload, SimulationInput } from "@/lib/api/decisionTypes";

export type RunSimulationPayload = {
  ruleId: string;
  input: SimulationInput;
};

const DECISION_ENDPOINT = "/api/bff/decision";

export const decisionSummaryQueryKey = ["decision", "summary"] as const;
export const decisionRulesQueryKey = ["decision", "rules"] as const;
export const simulationScenariosQueryKey = ["decision", "scenarios"] as const;

const buildResourceUrl = (resource: "rules" | "scenarios") => `${DECISION_ENDPOINT}?resource=${resource}`;

export async function fetchDecisionSummary(signal?: AbortSignal): Promise<DecisionSummary> {
  const response = await fetchFromBff<{ data: DecisionSummary }>(DECISION_ENDPOINT, {
    method: "GET",
    signal,
  });
  return response.data;
}
export const getDecisionSummary = fetchDecisionSummary;

export async function fetchDecisionRules(signal?: AbortSignal): Promise<Rule[]> {
  const response = await fetchFromBff<{ data: Rule[] }>(buildResourceUrl("rules"), {
    method: "GET",
    signal,
  });
  return response.data;
}

export async function fetchSimulationScenarios(signal?: AbortSignal): Promise<SimulationScenario[]> {
  const response = await fetchFromBff<{ data: SimulationScenario[] }>(buildResourceUrl("scenarios"), {
    method: "GET",
    signal,
  });
  return response.data;
}

export async function runSimulation(payload: RunSimulationPayload): Promise<SimulationScenario> {
  const response = await fetchFromBff<{ data: SimulationScenario }>(DECISION_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return response.data;
}

type UseDecisionSummaryQueryOptions = Omit<
  UseApiQueryOptions<DecisionSummary, ApiError, DecisionSummary, typeof decisionSummaryQueryKey>,
  "queryKey" | "queryFn"
>;

type UseDecisionRulesQueryOptions = Omit<
  UseApiQueryOptions<Rule[], ApiError, Rule[], typeof decisionRulesQueryKey>,
  "queryKey" | "queryFn"
>;

type UseSimulationScenariosQueryOptions = Omit<
  UseApiQueryOptions<SimulationScenario[], ApiError, SimulationScenario[], typeof simulationScenariosQueryKey>,
  "queryKey" | "queryFn"
>;

export function useDecisionSummaryQuery(options?: UseDecisionSummaryQueryOptions) {
  return useApiQuery<DecisionSummary, ApiError, DecisionSummary, typeof decisionSummaryQueryKey>({
    queryKey: decisionSummaryQueryKey,
    queryFn: ({ signal }) => fetchDecisionSummary(signal),
    ...options,
  });
}

export function useDecisionRulesQuery(options?: UseDecisionRulesQueryOptions) {
  return useApiQuery<Rule[], ApiError, Rule[], typeof decisionRulesQueryKey>({
    queryKey: decisionRulesQueryKey,
    queryFn: ({ signal }) => fetchDecisionRules(signal),
    ...options,
  });
}

export function useSimulationScenariosQuery(options?: UseSimulationScenariosQueryOptions) {
  return useApiQuery<SimulationScenario[], ApiError, SimulationScenario[], typeof simulationScenariosQueryKey>({
    queryKey: simulationScenariosQueryKey,
    queryFn: ({ signal }) => fetchSimulationScenarios(signal),
    ...options,
  });
}

type UseRunSimulationMutationOptions = Omit<
  UseMutationOptions<SimulationScenario, ApiError, RunSimulationPayload, unknown>,
  "mutationFn"
>;

export function useRunSimulationMutation(options?: UseRunSimulationMutationOptions) {
  return useApiMutation<SimulationScenario, ApiError, RunSimulationPayload>({
    mutationFn: runSimulation,
    ...options,
  });
}

export type { DecisionPayload, Rule, SimulationInput, SimulationScenario };
