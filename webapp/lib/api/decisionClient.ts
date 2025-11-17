import type { UseMutationOptions } from "@tanstack/react-query";

import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { ApiError } from "@/lib/api/apiError";
import { useApiMutation } from "@/lib/api/useApiMutation";
import { useApiQuery, type UseApiQueryOptions } from "@/lib/api/useApiQuery";

import type { TaskDecision } from "./inboxClient";

export type Rule = {
  id: string;
  name: string;
  description?: string;
  active: boolean;
  scope: "sku" | "vendor" | "category" | "global";
  params: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
};

export type SimulationScenarioResult = {
  summary: string;
  stats: Record<string, number>;
  sampleDecisions: TaskDecision[];
};

export type SimulationScenario = {
  id: string;
  name: string;
  description?: string;
  ruleId: string;
  input: Record<string, unknown>;
  result?: SimulationScenarioResult;
};

export type DecisionRulesResponse = {
  rules: Rule[];
};

export type SimulationScenariosResponse = {
  scenarios: SimulationScenario[];
};

export type RunSimulationPayload = {
  ruleId: string;
  input: Record<string, unknown>;
};

const DECISION_ENDPOINT = "/api/bff/decision";
const SIMULATION_ENDPOINT = "/api/bff/decision/simulate";

export const decisionRulesQueryKey = ["decision", "rules"] as const;
export const simulationScenariosQueryKey = ["decision", "scenarios"] as const;

const buildResourceUrl = (resource: "rules" | "scenarios") => `${DECISION_ENDPOINT}?resource=${resource}`;

export async function fetchDecisionRules(signal?: AbortSignal): Promise<DecisionRulesResponse> {
  return fetchFromBff<DecisionRulesResponse>(buildResourceUrl("rules"), {
    method: "GET",
    signal,
  });
}

export async function fetchSimulationScenarios(signal?: AbortSignal): Promise<SimulationScenariosResponse> {
  return fetchFromBff<SimulationScenariosResponse>(buildResourceUrl("scenarios"), {
    method: "GET",
    signal,
  });
}

export async function runSimulation(payload: RunSimulationPayload): Promise<SimulationScenario> {
  return fetchFromBff<SimulationScenario>(SIMULATION_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

type UseDecisionRulesQueryOptions = Omit<
  UseApiQueryOptions<DecisionRulesResponse, ApiError, DecisionRulesResponse, typeof decisionRulesQueryKey>,
  "queryKey" | "queryFn"
>;

type UseSimulationScenariosQueryOptions = Omit<
  UseApiQueryOptions<SimulationScenariosResponse, ApiError, SimulationScenariosResponse, typeof simulationScenariosQueryKey>,
  "queryKey" | "queryFn"
>;

export function useDecisionRulesQuery(options?: UseDecisionRulesQueryOptions) {
  return useApiQuery<DecisionRulesResponse, ApiError, DecisionRulesResponse, typeof decisionRulesQueryKey>({
    queryKey: decisionRulesQueryKey,
    queryFn: ({ signal }) => fetchDecisionRules(signal),
    ...options,
  });
}

export function useSimulationScenariosQuery(options?: UseSimulationScenariosQueryOptions) {
  return useApiQuery<
    SimulationScenariosResponse,
    ApiError,
    SimulationScenariosResponse,
    typeof simulationScenariosQueryKey
  >({
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
