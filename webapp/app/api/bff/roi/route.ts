import { NextRequest, NextResponse } from "next/server";

import { handleApiError, parseSortMeta, requirePermission, buildPaginationMeta } from "@/app/api/bff/utils";
import type { RoiItem } from "@/lib/api/bffTypes";
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
  const permission = await requirePermission("roi", "view");
  if (!permission.ok) {
    return permission.response;
  }

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

    const data = (apiResponse.items ?? []).map((item) => toRoiItem(item));

    const jsonResponse = {
      data,
      items: data,
      pagination: buildPaginationMeta(page, pageSize, total ?? 0),
      sort: parseSortMeta(state.sort ?? ROI_TABLE_DEFAULTS.sort ?? undefined),
      filters: normalizedFilters,
    };

    return NextResponse.json(jsonResponse);
  } catch (error) {
    return handleApiError(error, "Unable to load ROI rows.");
  }
}

const toNumberOrZero = (value?: number | null): number => (typeof value === "number" && Number.isFinite(value) ? value : 0);

const toRoiItem = (item: RoiListResponse["items"][number]): RoiItem => {
  const cost = toNumberOrZero(item.cost);
  const freight = toNumberOrZero(item.freight);
  const fees = toNumberOrZero(item.fees);
  const roiPct = toNumberOrZero(item.roi_pct);
  const buyPrice = cost + freight + fees;
  const margin = Number(((roiPct / 100) * buyPrice).toFixed(2));
  const sellPrice = Number((buyPrice + margin).toFixed(2));

  return {
    sku: item.asin ?? "",
    asin: item.asin ?? "",
    title: item.title ?? "",
    roi: roiPct,
    margin,
    currency: "EUR",
    buyPrice,
    sellPrice,
    salesRank: null,
    category: item.category ?? null,
    vendorId: item.vendor_id !== undefined && item.vendor_id !== null ? String(item.vendor_id) : null,
    fees: item.fees ?? null,
    freight: item.freight ?? null,
    cost: item.cost ?? null,
  };
};
