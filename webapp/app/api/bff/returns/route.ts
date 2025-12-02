import { NextRequest, NextResponse } from "next/server";

import { buildPaginationMeta, handleApiError, parseSortMeta, requirePermission } from "@/app/api/bff/utils";
import type { ReturnItem } from "@/lib/api/bffTypes";
import { returnsApiClient } from "@/lib/api/returnsApiClient";
import {
  RETURNS_TABLE_DEFAULTS,
  mergeReturnsTableStateWithDefaults,
  parseReturnsSearchParams,
  type ReturnsTableFilters,
  type ReturnsTableState,
} from "@/lib/tableState/returns";

import type { components, paths } from "@/lib/api/types.generated";

export const dynamic = "force-dynamic";

type ResourceType = "stats" | "list";

type ReturnsStatsResponse = paths["/stats/returns"]["get"]["responses"]["200"]["content"]["application/json"];
type ReturnsStatsItem = components["schemas"]["ReturnsStatsItem"];

type ReturnsSummaryResponse = {
  totalAsins: number;
  totalUnits: number;
  totalRefundAmount: number;
  avgRefundPerUnit: number;
  topAsin?: string | null;
  topAsinRefundAmount?: number | null;
};

const parseResource = (value: string | null): ResourceType => (value === "stats" ? "stats" : "list");

const normalizeFilters = (filters: ReturnsTableFilters | undefined): ReturnsTableFilters => ({
  dateFrom: filters?.dateFrom?.trim() ?? "",
  dateTo: filters?.dateTo?.trim() ?? "",
  vendor: filters?.vendor?.trim() ?? "",
  asin: filters?.asin?.trim() ?? "",
});

const BASE_DATE = Date.parse("2024-04-01T00:00:00.000Z");

const toListItem = (item: ReturnsStatsItem, page: number, index: number): ReturnItem => {
  const qty = typeof item.qty === "number" && Number.isFinite(item.qty) ? item.qty : 0;
  const refund = typeof item.refund_amount === "number" && Number.isFinite(item.refund_amount) ? item.refund_amount : 0;
  const returnId = item.asin ? `${item.asin}-${page}-${index}` : `return-${page}-${index}`;
  const timestamp = new Date(BASE_DATE + index * 60 * 60 * 1000).toISOString();

  return {
    returnId,
    asin: item.asin ?? "",
    sku: item.asin ?? "",
    reason: "not_provided",
    quantity: qty,
    reimbursementAmount: refund,
    currency: "EUR",
    status: refund > 0 ? "paid" : "pending",
    createdAt: timestamp,
    updatedAt: timestamp,
    avgRefundPerUnit: qty > 0 ? refund / qty : 0,
  };
};

const buildSummaryFallback = (items: ReturnsStatsItem[], totalReturns: number): ReturnsSummaryResponse => {
  const totals = items.reduce(
    (acc, item) => {
      const qty = typeof item.qty === "number" && Number.isFinite(item.qty) ? item.qty : 0;
      const refund = typeof item.refund_amount === "number" && Number.isFinite(item.refund_amount) ? item.refund_amount : 0;
      return {
        qty: acc.qty + qty,
        refund: acc.refund + refund,
      };
    },
    { qty: 0, refund: 0 }
  );

  const top = [...items].sort((a, b) => (b.refund_amount ?? 0) - (a.refund_amount ?? 0))[0];

  return {
    totalAsins: totalReturns,
    totalUnits: Math.round(totals.qty),
    totalRefundAmount: totals.refund,
    avgRefundPerUnit: totals.qty > 0 ? totals.refund / totals.qty : 0,
    topAsin: top?.asin ?? null,
    topAsinRefundAmount: typeof top?.refund_amount === "number" ? top.refund_amount : null,
  };
};

const buildListResponse = (
  apiResponse: ReturnsStatsResponse,
  fallback: Pick<ReturnsTableState, "page" | "pageSize">,
  filters: ReturnsTableFilters,
  sortValue?: string | null
) => {
  const pagination = apiResponse.pagination;
  const page = pagination?.page ?? fallback.page;
  const pageSize = pagination?.page_size ?? fallback.pageSize;
  const total = pagination?.total ?? apiResponse.total_returns ?? apiResponse.items?.length ?? 0;

  const mapped = (apiResponse.items ?? []).map((item, index) => toListItem(item, page, index));

  return {
    data: mapped,
    items: mapped,
    pagination: buildPaginationMeta(page, pageSize, total),
    sort: parseSortMeta(sortValue),
    filters,
    summary: buildSummaryResponse(apiResponse),
  };
};

const buildSummaryResponse = (apiResponse: ReturnsStatsResponse): ReturnsSummaryResponse => {
  const summary = apiResponse.summary;
  if (summary) {
    const totalAsins = summary.total_asins ?? apiResponse.total_returns ?? apiResponse.items?.length ?? 0;
    return {
      totalAsins,
      totalUnits: summary.total_units ?? 0,
      totalRefundAmount: summary.total_refund_amount ?? 0,
      avgRefundPerUnit: summary.avg_refund_per_unit ?? 0,
      topAsin: summary.top_asin ?? null,
      topAsinRefundAmount: summary.top_refund_amount ?? null,
    };
  }
  return buildSummaryFallback(apiResponse.items ?? [], apiResponse.total_returns ?? apiResponse.items?.length ?? 0);
};

export async function GET(request: NextRequest) {
  const permission = await requirePermission("returns", "view");
  if (!permission.ok) {
    return permission.response;
  }

  const params = request.nextUrl.searchParams;
  const resource = parseResource(params.get("resource"));
  const parsedState = parseReturnsSearchParams(params);
  const state = mergeReturnsTableStateWithDefaults(parsedState);
  const filters = normalizeFilters(state.filters);

  try {
    if (resource === "stats") {
      const statsResponse = await returnsApiClient.fetchStats({
        page: 1,
        pageSize: 1,
        sort: RETURNS_TABLE_DEFAULTS.sort ?? "refund_desc",
        filters,
      });
      return NextResponse.json({ data: buildSummaryResponse(statsResponse) });
    }

    const apiResponse = await returnsApiClient.fetchStats({
      page: state.page,
      pageSize: state.pageSize,
      sort: state.sort ?? RETURNS_TABLE_DEFAULTS.sort ?? "refund_desc",
      filters,
    });

    return NextResponse.json(
      buildListResponse(apiResponse, { page: state.page, pageSize: state.pageSize }, filters, state.sort)
    );
  } catch (error) {
    return handleApiError(error, "Unable to load returns data.");
  }
}

const methodNotAllowed = () =>
  NextResponse.json(
    { error: { code: "METHOD_NOT_ALLOWED", message: "Only GET is supported for this endpoint." } },
    {
      status: 405,
      headers: {
        Allow: "GET",
      },
    }
  );

export const POST = methodNotAllowed;
export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
export const DELETE = methodNotAllowed;
