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

type RoiRow = components["schemas"]["RoiRow"];

export const dynamic = "force-dynamic";

const OBSERVE_ONLY_ROI_THRESHOLD = 20;

const getMarginValue = (row: RoiRow): number => {
  const roiPercent = row.roi_pct ?? 0;
  const cost = (row.cost ?? 0) + (row.freight ?? 0) + (row.fees ?? 0);
  return (roiPercent / 100) * cost;
};

const compareNumbers = (a: number | null | undefined, b: number | null | undefined) => {
  const left = typeof a === "number" && Number.isFinite(a) ? a : Number.NEGATIVE_INFINITY;
  const right = typeof b === "number" && Number.isFinite(b) ? b : Number.NEGATIVE_INFINITY;
  return left - right;
};

const comparators: Record<RoiSort, (a: RoiRow, b: RoiRow) => number> = {
  roi_pct_desc: (a, b) => compareNumbers(b.roi_pct, a.roi_pct),
  roi_pct_asc: (a, b) => compareNumbers(a.roi_pct, b.roi_pct),
  asin_asc: (a, b) => (a.asin ?? "").localeCompare(b.asin ?? ""),
  asin_desc: (a, b) => (b.asin ?? "").localeCompare(a.asin ?? ""),
  margin_desc: (a, b) => getMarginValue(b) - getMarginValue(a),
  margin_asc: (a, b) => getMarginValue(a) - getMarginValue(b),
  vendor_asc: (a, b) => String(a.vendor_id ?? "").localeCompare(String(b.vendor_id ?? "")),
  vendor_desc: (a, b) => String(b.vendor_id ?? "").localeCompare(String(a.vendor_id ?? "")),
};

const applyFilters = (rows: RoiRow[], filters: RoiTableFilters): RoiRow[] => {
  const vendor = filters.vendor?.trim();
  const category = filters.category?.trim().toLowerCase();
  const search = filters.search?.trim().toLowerCase();
  const roiMin = typeof filters.roiMin === "number" && Number.isFinite(filters.roiMin) ? filters.roiMin : undefined;

  return rows.filter((row) => {
    if (roiMin !== undefined) {
      const value = row.roi_pct ?? 0;
      if (value < roiMin) {
        return false;
      }
    }

    if (vendor) {
      if (String(row.vendor_id ?? "").trim() !== vendor) {
        return false;
      }
    }

    if (category) {
      if ((row.category ?? "").toLowerCase() !== category) {
        return false;
      }
    }

    if (filters.observeOnly) {
      const roiPct = row.roi_pct ?? 0;
      if (roiPct > OBSERVE_ONLY_ROI_THRESHOLD) {
        return false;
      }
    }

    if (search) {
      const haystacks = [row.asin ?? "", row.title ?? ""].map((value) => value.toLowerCase());
      if (!haystacks.some((value) => value.includes(search))) {
        return false;
      }
    }

    return true;
  });
};

const sortRows = (rows: RoiRow[], sort: RoiSort | undefined): RoiRow[] => {
  const key = sort ?? ROI_TABLE_DEFAULTS.sort ?? "roi_pct_desc";
  const comparator = comparators[key] ?? comparators.roi_pct_desc;
  return [...rows].sort(comparator);
};

const paginateRows = (rows: RoiRow[], page: number, pageSize: number) => {
  const total = rows.length;
  const totalPages = total > 0 ? Math.ceil(total / pageSize) : 1;
  const safePage = Math.min(Math.max(page, 1), Math.max(totalPages, 1));
  const start = (safePage - 1) * pageSize;
  const items = rows.slice(start, start + pageSize);

  return {
    items,
    pagination: {
      page: safePage,
      pageSize,
      total,
      totalPages,
    },
  };
};

export async function GET(request: NextRequest) {
  try {
    const partial = parseRoiSearchParams(request.nextUrl.searchParams);
    const state = mergeRoiTableStateWithDefaults(partial);

    const filters = state.filters ?? ROI_TABLE_DEFAULTS.filters ?? {};
    const apiRows = await roiClient.listRoiRows({
      roiMin: filters.roiMin ?? null,
      vendor: filters.vendor ?? null,
      category: filters.category ?? null,
    });

    const filteredRows = applyFilters(apiRows, filters);
    const sortedRows = sortRows(filteredRows, state.sort);
    const result = paginateRows(sortedRows, state.page, state.pageSize);

    return NextResponse.json(result);
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
