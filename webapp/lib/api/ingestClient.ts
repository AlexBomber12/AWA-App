import { fetchFromBff } from "@/lib/api/fetchFromBff";
import type { paths } from "@/lib/api/types.generated";

export type IngestStartRequest = {
  uri?: string | null;
  report_type?: string | null;
  force?: boolean;
  file?: File | Blob | null;
};

export type IngestJobStatus = paths["/jobs/{task_id}"]["get"]["responses"]["200"]["content"]["application/json"];

const INGEST_ENDPOINT = "/api/bff/ingest";
const INGEST_JOB_ENDPOINT = "/api/bff/ingest/jobs";

const buildQueryString = ({ uri, report_type, force }: IngestStartRequest): string => {
  const query = new URLSearchParams();

  const normalizedUri = typeof uri === "string" ? uri.trim() : uri ?? undefined;
  if (normalizedUri) {
    query.set("uri", normalizedUri);
  }

  if (typeof report_type === "string" && report_type.trim()) {
    query.set("report_type", report_type.trim());
  }

  if (typeof force === "boolean") {
    query.set("force", String(force));
  }

  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
};

export async function startIngestJob(payload: IngestStartRequest): Promise<IngestJobStatus> {
  const { file, ...params } = payload;
  const query = buildQueryString(params);
  const targetUrl = `${INGEST_ENDPOINT}${query}`;

  let body: FormData | undefined;
  if (file instanceof File || file instanceof Blob) {
    body = new FormData();
    body.set("file", file);
  }

  return fetchFromBff<IngestJobStatus>(targetUrl, {
    method: "POST",
    body,
  });
}

export async function getIngestJobStatus(taskId: string): Promise<IngestJobStatus> {
  if (!taskId) {
    throw new Error("taskId is required to fetch ingest job status");
  }

  const encoded = encodeURIComponent(taskId);
  return fetchFromBff<IngestJobStatus>(`${INGEST_JOB_ENDPOINT}/${encoded}`);
}
