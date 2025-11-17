import { fetchFromBff } from "@/lib/api/fetchFromBff";

import type { paths } from "./types.generated";

type KpiResponse = paths["/stats/kpi"]["get"]["responses"]["200"]["content"]["application/json"];
type RoiTrendResponse = paths["/stats/roi_trend"]["get"]["responses"]["200"]["content"]["application/json"];

export type StatsKpi = KpiResponse["kpi"];
export type DashboardStatsResponse = {
  kpi: StatsKpi;
  roiTrend: RoiTrendResponse;
};

const BFF_STATS_ENDPOINT = "/api/bff/stats";
let inFlightStatsRequest: Promise<DashboardStatsResponse> | null = null;

const loadStats = () => {
  if (!inFlightStatsRequest) {
    inFlightStatsRequest = fetchFromBff<DashboardStatsResponse>(BFF_STATS_ENDPOINT).finally(() => {
      inFlightStatsRequest = null;
    });
  }
  return inFlightStatsRequest;
};

export const statsClient = {
  async getKpi(): Promise<StatsKpi> {
    const result = await loadStats();
    return result.kpi;
  },
  async getRoiTrend(): Promise<RoiTrendResponse> {
    const result = await loadStats();
    return result.roiTrend;
  },
  async getDashboardStats(): Promise<DashboardStatsResponse> {
    return loadStats();
  },
};
