import { NextRequest, NextResponse } from "next/server";

import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import type { components } from "@/lib/api/types.generated";

export const dynamic = "force-dynamic";

const RETURNS_API_PATH = "/stats/returns";
const DEFAULT_PAGE = 1;
const DEFAULT_PAGE_SIZE = 25;
const MAX_PAGE_SIZE = 100;

const SORT_OPTIONS = ["refund_desc", "refund_asc", "qty_desc", "qty_asc", "asin_asc", "asin_desc"] as const;
type ReturnsSort = (typeof SORT_OPTIONS)[number];

type ReturnsStatsResponse = components["schemas"]["ReturnsStatsResponse"];
type ReturnsStatsItem = components["schemas"]["ReturnsStatsItem"];

type ReturnsListItem = {
  asin: string;
  qty: number;
  refundAmount: number;
  avgRefundPerUnit: number;
};

type ReturnsListResponse = {
  items: ReturnsListItem[];
  pagination: {
    page: number;
    pageSize: number;
    total: number;
    totalPages: number;
  };
};

type ReturnsSummaryResponse = {
  totalAsins: number;
  totalUnits: number;
  totalRefundAmount: number;
  avgRefundPerUnit: number;
  topAsin?: string | null;
  topAsinRefundAmount?: number | null;
};

type ResourceType = "stats" | "list";

const parseResource = (value: string | null): ResourceType => {
  if (value === "stats") {
    return "stats";
  }
  return "list";
};

const parsePositiveInt = (value: string | null, fallback: number, max?: number) => {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  const normalized = Math.floor(parsed);
  if (max && normalized > max) {
    return max;
  }
  return normalized;
};

const parseSort = (value: string | null): ReturnsSort => {
  if (value && SORT_OPTIONS.includes(value as ReturnsSort)) {
    return value as ReturnsSort;
  }
  return "refund_desc";
};

const applyFiltersToQuery = (source: URLSearchParams, target: URLSearchParams) => {
  const passthroughKeys: Record<string, string> = {
    "filter[date_from]": "date_from",
    "filter[date_to]": "date_to",
    "filter[vendor]": "vendor",
    "filter[asin]": "asin",
  };

  Object.entries(passthroughKeys).forEach(([sourceKey, targetKey]) => {
    const value = source.get(sourceKey);
    if (value) {
      target.set(targetKey, value);
    }
  });
};

const toListItem = (item: ReturnsStatsItem): ReturnsListItem => {
  const qty = typeof item.qty === "number" && Number.isFinite(item.qty) ? item.qty : 0;
  const refund = typeof item.refund_amount === "number" && Number.isFinite(item.refund_amount) ? item.refund_amount : 0;
  return {
    asin: item.asin ?? "",
    qty,
    refundAmount: refund,
    avgRefundPerUnit: qty > 0 ? refund / qty : 0,
  };
};

const buildSummary = (items: ReturnsStatsItem[], totalReturns: number): ReturnsSummaryResponse => {
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
  page: number,
  pageSize: number
): ReturnsListResponse => {
  const pagination = apiResponse.pagination;
  const total = pagination?.total ?? apiResponse.total_returns ?? apiResponse.items?.length ?? 0;
  const totalPages = pagination?.total_pages ?? (total > 0 ? Math.ceil(total / pageSize) : 1);
  return {
    items: (apiResponse.items ?? []).map(toListItem),
    pagination: {
      page: pagination?.page ?? page,
      pageSize: pagination?.page_size ?? pageSize,
      total,
      totalPages,
    },
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
  return buildSummary(apiResponse.items ?? [], apiResponse.total_returns ?? apiResponse.items?.length ?? 0);
};

async function fetchReturnsStats(params: URLSearchParams): Promise<ReturnsStatsResponse> {
  const query = params.toString();
  const path = query ? `${RETURNS_API_PATH}?${query}` : RETURNS_API_PATH;
  return fetchFromApi<ReturnsStatsResponse>(path);
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const resource = parseResource(params.get("resource"));
  const filterParams = new URLSearchParams();
  applyFiltersToQuery(params, filterParams);

  try {
    if (resource === "stats") {
      const statsParams = new URLSearchParams(filterParams);
      statsParams.set("page", "1");
      statsParams.set("page_size", "1");
      statsParams.set("sort", "refund_desc");
      const statsResponse = await fetchReturnsStats(statsParams);
      return NextResponse.json(buildSummaryResponse(statsResponse));
    }

    const page = parsePositiveInt(params.get("page"), DEFAULT_PAGE);
    const pageSize = parsePositiveInt(params.get("page_size"), DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE);
    const sort = parseSort(params.get("sort"));

    const listParams = new URLSearchParams(filterParams);
    listParams.set("page", String(page));
    listParams.set("page_size", String(pageSize));
    listParams.set("sort", sort);
    const apiResponse = await fetchReturnsStats(listParams);
    const response = buildListResponse(apiResponse, page, pageSize);

    return NextResponse.json(response);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled Returns BFF error", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to load returns data.", status: 500 },
      { status: 500 }
    );
  }
}

const methodNotAllowed = () =>
  NextResponse.json(
    { code: "METHOD_NOT_ALLOWED", message: "Only GET is supported for this endpoint." },
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
