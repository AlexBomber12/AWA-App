import { NextRequest, NextResponse } from "next/server";

import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import type { paths } from "@/lib/api/types.generated";

export const dynamic = "force-dynamic";

type IngestStartResponse = paths["/ingest"]["post"]["responses"]["200"]["content"]["application/json"];
type IngestJobStatus = paths["/jobs/{task_id}"]["get"]["responses"]["200"]["content"]["application/json"];

const ALLOWED_QUERY_PARAMS = new Set(["uri", "report_type", "force"]);

const buildForwardedQuery = (request: NextRequest) => {
  const forwarded = new URLSearchParams();
  request.nextUrl.searchParams.forEach((value, key) => {
    if (ALLOWED_QUERY_PARAMS.has(key)) {
      forwarded.set(key, value);
    }
  });
  const query = forwarded.toString();
  return query ? `?${query}` : "";
};

const readJsonBody = async (request: NextRequest) => {
  try {
    const payload = await request.json();
    if (payload && typeof payload === "object") {
      return JSON.stringify(payload);
    }
    return undefined;
  } catch {
    return undefined;
  }
};

export async function POST(request: NextRequest) {
  try {
    const query = buildForwardedQuery(request);
    const contentType = request.headers.get("content-type") ?? "";
    let body: BodyInit | undefined;
    const headers: HeadersInit = {};

    if (contentType.includes("application/json")) {
      const jsonBody = await readJsonBody(request);
      if (jsonBody) {
        headers["Content-Type"] = "application/json";
        body = jsonBody;
      }
    } else if (contentType.includes("multipart/form-data")) {
      const formData = await request.formData();
      if ([...formData.keys()].length > 0) {
        body = formData;
      }
    }

    const submission = await fetchFromApi<IngestStartResponse>(`/ingest${query}`, {
      method: "POST",
      body,
      headers,
    });

    const taskId =
      submission && typeof submission === "object" && "task_id" in submission
        ? String((submission as { task_id?: string }).task_id ?? "")
        : "";

    if (!taskId) {
      return NextResponse.json(submission ?? {});
    }

    const jobStatus = await fetchFromApi<IngestJobStatus>(`/jobs/${encodeURIComponent(taskId)}`);

    return NextResponse.json(jobStatus);
  } catch (error) {
    if (isApiError(error)) {
      return NextResponse.json(
        { code: error.code, message: error.message, status: error.status, details: error.details },
        { status: error.status }
      );
    }

    console.error("Unhandled ingest BFF error", error);
    return NextResponse.json(
      { code: "BFF_ERROR", message: "Unable to submit ingest job.", status: 500 },
      { status: 500 }
    );
  }
}

const methodNotAllowed = () =>
  NextResponse.json(
    { code: "METHOD_NOT_ALLOWED", message: "Only POST is supported for this endpoint." },
    {
      status: 405,
      headers: {
        Allow: "POST",
      },
    }
  );

export const GET = methodNotAllowed;
export const PUT = methodNotAllowed;
export const PATCH = methodNotAllowed;
export const DELETE = methodNotAllowed;
