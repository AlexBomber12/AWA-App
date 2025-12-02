import type { RoiItem } from "@/lib/api/bffTypes";
import type { RoiPageResponse } from "@/lib/api/roiClient";
import type { components } from "@/lib/api/types.generated";

export type RoiApprovalResponse = components["schemas"]["RoiApprovalResponse"];
export type RoiListResponse = RoiPageResponse;

export type { RoiItem };
