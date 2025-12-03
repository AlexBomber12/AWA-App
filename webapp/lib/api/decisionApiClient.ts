import { fetchFromApi } from "@/lib/api/fetchFromApi";

import type { paths } from "./types.generated";

type DecisionPreviewResponse = paths["/decision/preview"]["get"]["responses"]["200"]["content"]["application/json"];
type DecisionRunResponse = paths["/decision/run"]["post"]["responses"]["200"]["content"]["application/json"];

export type DecisionRunParams = {
  limit?: number;
};

export const decisionApiClient = {
  preview(params?: DecisionRunParams): Promise<DecisionPreviewResponse> {
    const query = new URLSearchParams();
    if (params?.limit) {
      query.set("limit", String(params.limit));
    }
    const suffix = query.toString();
    const path = suffix ? `/decision/preview?${suffix}` : "/decision/preview";
    return fetchFromApi<DecisionPreviewResponse>(path);
  },

  run(params?: DecisionRunParams): Promise<DecisionRunResponse> {
    const query = new URLSearchParams();
    if (params?.limit) {
      query.set("limit", String(params.limit));
    }
    const suffix = query.toString();
    const path = suffix ? `/decision/run?${suffix}` : "/decision/run";
    return fetchFromApi<DecisionRunResponse>(path, { method: "POST" });
  },
};
