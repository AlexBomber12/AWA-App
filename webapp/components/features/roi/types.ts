import type { RoiRow, RoiTableResponse } from "@/lib/api/roiClient";
import type { components } from "@/lib/api/types.generated";

export type RoiApprovalResponse = components["schemas"]["RoiApprovalResponse"];
export type RoiListResponse = RoiTableResponse;

export type { RoiRow };
