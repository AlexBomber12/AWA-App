import { NextRequest, NextResponse } from "next/server";

import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import type { paths } from "@/lib/api/types.generated";
import { getServerAuthSession } from "@/lib/auth";

export type SkuDetailResponse = paths["/sku/{asin}"]["get"]["responses"]["200"]["content"]["application/json"];

const buildApiPath = (asin: string, request: NextRequest) => {
  const params = request.nextUrl.searchParams;
  const passthrough = new URLSearchParams(params);
  passthrough.delete("asin");
  const query = passthrough.toString();
  const encodedAsin = encodeURIComponent(asin);
  return query ? `/sku/${encodedAsin}?${query}` : `/sku/${encodedAsin}`;
};

export async function GET(request: NextRequest) {
  const session = await getServerAuthSession();
  if (!session) {
    return NextResponse.json(
      { code: "UNAUTHORIZED", message: "Authentication required.", status: 401 },
      { status: 401 }
    );
  }

  const asin = request.nextUrl.searchParams.get("asin");
  if (!asin) {
    return NextResponse.json(
      { code: "INVALID_REQUEST", message: "Missing required asin parameter.", status: 400 },
      { status: 400 }
    );
  }

  try {
    const path = buildApiPath(asin, request);
    const detail = await fetchFromApi<SkuDetailResponse>(path);
    return NextResponse.json(detail);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled SKU BFF error", { asin, error });
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to load SKU detail.", status: 500 },
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
