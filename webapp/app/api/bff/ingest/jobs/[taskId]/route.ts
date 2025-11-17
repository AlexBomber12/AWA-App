import { NextRequest, NextResponse } from "next/server";

import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import type { paths } from "@/lib/api/types.generated";

export const dynamic = "force-dynamic";

type IngestJobStatus = paths["/jobs/{task_id}"]["get"]["responses"]["200"]["content"]["application/json"];

type RouteContext = {
  params: {
    taskId?: string;
  };
};

export async function GET(_request: NextRequest, context: RouteContext) {
  const taskId = context.params?.taskId;
  if (!taskId) {
    return NextResponse.json(
      { code: "INVALID_REQUEST", message: "Missing taskId.", status: 400 },
      { status: 400 }
    );
  }

  try {
    const status = await fetchFromApi<IngestJobStatus>(`/jobs/${encodeURIComponent(taskId)}`);
    return NextResponse.json(status);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled ingest job status BFF error", { taskId, error });
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to load ingest job status.", status: 500 },
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
