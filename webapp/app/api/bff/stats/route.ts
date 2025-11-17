import { NextResponse } from "next/server";

import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import type { paths } from "@/lib/api/types.generated";
import { getServerAuthSession } from "@/lib/auth";

type KpiResponse = paths["/stats/kpi"]["get"]["responses"]["200"]["content"]["application/json"];
type RoiTrendResponse = paths["/stats/roi_trend"]["get"]["responses"]["200"]["content"]["application/json"];

export async function GET() {
  const session = await getServerAuthSession();
  if (!session) {
    return NextResponse.json(
      { code: "UNAUTHORIZED", message: "Authentication required.", status: 401 },
      { status: 401 }
    );
  }

  try {
    const [kpiResponse, roiTrend] = await Promise.all([
      fetchFromApi<KpiResponse>("/stats/kpi"),
      fetchFromApi<RoiTrendResponse>("/stats/roi_trend"),
    ]);

    return NextResponse.json({
      kpi: kpiResponse.kpi,
      roiTrend,
    });
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled BFF stats error", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to fetch stats.", status: 500 },
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
