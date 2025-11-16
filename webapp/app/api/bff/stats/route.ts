import { NextResponse } from "next/server";

import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import { getServerAuthSession } from "@/lib/auth";

export async function GET() {
  const session = await getServerAuthSession();
  if (!session) {
    return NextResponse.json(
      { code: "UNAUTHORIZED", message: "Authentication required." },
      { status: 401 }
    );
  }

  try {
    const data = await fetchFromApi("/stats/kpi");
    return NextResponse.json(data);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message },
        { status: error.status }
      );
    }

    console.error("Unhandled BFF stats error", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to fetch KPI stats." },
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
