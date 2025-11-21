import { NextRequest, NextResponse } from "next/server";

import { isApiError } from "@/lib/api/fetchFromApi";
import { roiApiClient } from "@/lib/api/roiApiClient";
import {
  ROI_TABLE_DEFAULTS,
  mergeRoiTableStateWithDefaults,
  parseRoiSearchParams,
  type RoiTableFilters,
} from "@/lib/tableState/roi";

import type { paths } from "@/lib/api/types.generated";

type RoiListResponse = paths["/roi"]["get"]["responses"]["200"]["content"]["application/json"];

export const dynamic = "force-dynamic";

const OBSERVE_ONLY_ROI_THRESHOLD = 20;

export async function GET(request: NextRequest) {
  try {
    const partial = parseRoiSearchParams(request.nextUrl.searchParams);
    const state = mergeRoiTableStateWithDefaults(partial);

    const filters: RoiTableFilters = state.filters ?? ROI_TABLE_DEFAULTS.filters ?? {};
    const observeOnly = Boolean(filters.observeOnly);
    const vendorCandidate = filters.vendor?.trim();
    const vendorFilter =
      vendorCandidate && Number.isFinite(Number(vendorCandidate)) ? Number(vendorCandidate) : null;
    const categoryFilter = filters.category?.trim();
    const searchFilter = filters.search?.trim();
    const normalizedFilters: RoiTableFilters = {
      ...filters,
      vendor: vendorFilter !== null ? String(vendorFilter) : undefined,
      category: categoryFilter ?? undefined,
      search: searchFilter ?? undefined,
    };

    const apiResponse: RoiListResponse = await roiApiClient.listRoiRows({
      page: state.page,
      pageSize: state.pageSize,
      sort: state.sort ?? ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc",
      filters: normalizedFilters,
      roiMax: observeOnly ? OBSERVE_ONLY_ROI_THRESHOLD : undefined,
    });

    const pagination = apiResponse.pagination;
    const page = pagination?.page ?? state.page;
    const pageSize = pagination?.page_size ?? state.pageSize;
    const total = pagination?.total ?? apiResponse.items?.length ?? 0;
    const totalPages = pagination?.total_pages ?? (total > 0 ? Math.ceil(total / pageSize) : 1);

    const jsonResponse = {
      items: apiResponse.items ?? [],
      pagination: {
        page,
        pageSize,
        total,
        totalPages,
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
