import { NextRequest, NextResponse } from "next/server";

import { isApiError } from "@/lib/api/fetchFromApi";
import { roiClient } from "@/lib/api/roiClient";

import type { components } from "@/lib/api/types.generated";
import {
  ROI_TABLE_DEFAULTS,
  mergeRoiTableStateWithDefaults,
  parseRoiSearchParams,
  type RoiSort,
  type RoiTableFilters,
} from "@/components/features/roi/tableState";

type RoiListResponse = components["schemas"]["RoiListResponse"];

export const dynamic = "force-dynamic";

const OBSERVE_ONLY_ROI_THRESHOLD = 20;

export async function GET(request: NextRequest) {
  try {
    const partial = parseRoiSearchParams(request.nextUrl.searchParams);
    const state = mergeRoiTableStateWithDefaults(partial);

    const filters = state.filters ?? ROI_TABLE_DEFAULTS.filters ?? {};
    const observeOnly = Boolean(filters.observeOnly);
    const vendorCandidate = filters.vendor?.trim();
    const vendorFilter =
      vendorCandidate && Number.isFinite(Number(vendorCandidate)) ? Number(vendorCandidate) : null;
    const categoryFilter = filters.category?.trim();
    const searchFilter = filters.search?.trim();
    const apiResponse: RoiListResponse = await roiClient.listRoiRows({
      page: state.page,
      pageSize: state.pageSize,
      sort: state.sort ?? ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc",
      roiMin: filters.roiMin ?? null,
      roiMax: observeOnly ? OBSERVE_ONLY_ROI_THRESHOLD : undefined,
      vendor: vendorFilter,
      category: categoryFilter ?? null,
      search: searchFilter ?? null,
    });

    const pagination = apiResponse.pagination;
    const jsonResponse = {
      items: apiResponse.items ?? [],
      pagination: {
        page: pagination?.page ?? state.page,
        pageSize: pagination?.page_size ?? state.pageSize,
        total: pagination?.total ?? apiResponse.items?.length ?? 0,
        totalPages: pagination?.total_pages ?? 1,
      },
    };

    return NextResponse.json(jsonResponse);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled ROI BFF error", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to load ROI rows.", status: 500 },
      { status: 500 }
    );
  }
}
