import { createApiError, type ApiError } from "@/lib/api/apiError";

const buildBffUrl = (path: string): string => {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const base =
    process.env.NEXT_PUBLIC_WEBAPP_URL ??
    (typeof window !== "undefined" && window.location ? window.location.origin : undefined) ??
    "http://localhost:3000";

  return new URL(normalizedPath, base).toString();
};

const readPayload = async (response: Response) => {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    try {
      return await response.json();
    } catch {
      return undefined;
    }
  }

  try {
    return await response.text();
  } catch {
    return undefined;
  }
};

const toApiError = (status: number, payload: unknown): ApiError => {
  if (payload && typeof payload === "object") {
    if ("error" in (payload as Record<string, unknown>)) {
      const nested = (payload as { error?: { code?: string; message?: string; status?: number; details?: unknown } }).error;
      return createApiError({
        code: nested?.code ?? "BFF_ERROR",
        message: nested?.message ?? "Unexpected response from BFF.",
        status: status ?? nested?.status ?? 500,
        details: nested?.details ?? payload,
      });
    }

    if ("code" in payload && "message" in payload) {
      const errorPayload = payload as { code: string; message: string; details?: unknown; status?: number };
      return createApiError({
        code: errorPayload.code ?? "BFF_ERROR",
        message: errorPayload.message ?? "Unexpected response from BFF.",
        status: status ?? errorPayload.status ?? 500,
        details: errorPayload.details ?? payload,
      });
    }
  }

  return createApiError({
    code: "BFF_ERROR",
    message: `BFF request failed with status ${status}`,
    status,
    details: payload,
  });
};

export async function fetchFromBff<T>(path: string, init?: RequestInit): Promise<T> {
  const url = buildBffUrl(path);
  const response = await fetch(url, {
    credentials: "same-origin",
    ...init,
  });

  if (response.ok) {
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  const details = await readPayload(response);

  console.error("fetchFromBff failed", {
    path,
    status: response.status,
    details,
  });

  throw toApiError(response.status, details);
}
