import { NextRequest, NextResponse } from "next/server";

import { isApiError } from "@/lib/api/fetchFromApi";
import { roiApiClient } from "@/lib/api/roiApiClient";

const normalizeAsins = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === "string" ? item.trim() : ""))
    .filter((asin) => Boolean(asin));
};

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json().catch(() => null);
    const asins = normalizeAsins(payload?.asins);
    if (!asins.length) {
      return NextResponse.json(
        { code: "INVALID_REQUEST", message: "Select at least one SKU to approve.", status: 400 },
        { status: 400 }
      );
    }

    const response = await roiApiClient.bulkApproveRoi({ asins });

    return NextResponse.json(response);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled ROI bulk approve BFF error", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to approve ROI rows.", status: 500 },
      { status: 500 }
    );
  }
}
