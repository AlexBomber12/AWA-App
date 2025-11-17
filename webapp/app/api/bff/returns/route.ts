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

const sortItems = (items: ReturnsStatsItem[], sort: ReturnsSort): ReturnsStatsItem[] => {
  const normalizeNumber = (value: number | null | undefined) => (typeof value === "number" && Number.isFinite(value) ? value : 0);
  const normalized = [...items];
  normalized.sort((a, b) => {
    const aRefund = normalizeNumber(a.refund_amount);
    const bRefund = normalizeNumber(b.refund_amount);
    const aQty = normalizeNumber(a.qty);
    const bQty = normalizeNumber(b.qty);
    const aAsin = a.asin ?? "";
    const bAsin = b.asin ?? "";

    switch (sort) {
      case "refund_asc":
        return aRefund - bRefund;
      case "refund_desc":
        return bRefund - aRefund;
      case "qty_asc":
        return aQty - bQty;
      case "qty_desc":
        return bQty - aQty;
      case "asin_desc":
        return bAsin.localeCompare(aAsin);
      case "asin_asc":
      default:
        return aAsin.localeCompare(bAsin);
    }
  });
  return normalized;
};

const paginateItems = (items: ReturnsStatsItem[], page: number, pageSize: number) => {
  const total = items.length;
  const totalPages = total > 0 ? Math.ceil(total / pageSize) : 1;
  const safePage = Math.min(Math.max(page, 1), Math.max(totalPages, 1));
  const start = (safePage - 1) * pageSize;
  const slice = items.slice(start, start + pageSize);
  return {
    slice,
    pagination: {
      page: safePage,
      pageSize,
      total,
      totalPages,
    },
  };
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

async function fetchReturnsStats(params: URLSearchParams): Promise<ReturnsStatsResponse> {
  const fastApiParams = new URLSearchParams();
  applyFiltersToQuery(params, fastApiParams);
  const query = fastApiParams.toString();
  const path = query ? `${RETURNS_API_PATH}?${query}` : RETURNS_API_PATH;
  return fetchFromApi<ReturnsStatsResponse>(path);
}

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const resource = parseResource(params.get("resource"));

  try {
    const stats = await fetchReturnsStats(params);
    const items = stats.items ?? [];

    if (resource === "stats") {
      return NextResponse.json(buildSummary(items, stats.total_returns ?? items.length));
    }

    const page = parsePositiveInt(params.get("page"), DEFAULT_PAGE);
    const pageSize = parsePositiveInt(params.get("page_size"), DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE);
    const sort = parseSort(params.get("sort"));

    const sorted = sortItems(items, sort);
    const { slice, pagination } = paginateItems(sorted, page, pageSize);
    const response: ReturnsListResponse = {
      items: slice.map(toListItem),
      pagination,
    };

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
