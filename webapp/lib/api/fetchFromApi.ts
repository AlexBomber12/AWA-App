import { getServerAuthSession } from "@/lib/auth";

export type ApiError = {
  code: string;
  message: string;
  status: number;
  details?: unknown;
};

export const isApiError = (value: unknown): value is ApiError => {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    "message" in value &&
    "status" in value
  );
};

const buildApiUrl = (path: string): URL => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!baseUrl) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured.");
  }
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return new URL(normalizedPath, baseUrl);
};

const createApiError = (params: ApiError): ApiError => params;

const parseErrorMessage = (details: unknown): string | undefined => {
  if (!details) {
    return undefined;
  }

  if (typeof details === "string") {
    return details;
  }

  if (typeof details === "object") {
    if ("message" in details && typeof details.message === "string") {
      return details.message;
    }
    if ("detail" in details && typeof details.detail === "string") {
      return details.detail;
    }
  }

  return undefined;
};

const readErrorPayload = async (response: Response) => {
  const contentType = response.headers.get("content-type");
  if (contentType?.includes("application/json")) {
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

// Pattern: use this for new BFF endpoints so future work and Codex can reuse this helper.
export async function fetchFromApi<T>(path: string, init?: RequestInit): Promise<T> {
  const session = await getServerAuthSession();
  const accessToken = session?.accessToken;

  if (!accessToken) {
    throw createApiError({
      code: "UNAUTHORIZED",
      message: "Authentication required.",
      status: 401,
    });
  }

  const url = buildApiUrl(path);
  const headers = new Headers(init?.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (response.ok) {
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  if (response.status === 401 || response.status === 403) {
    throw createApiError({
      code: response.status === 401 ? "UNAUTHORIZED" : "FORBIDDEN",
      message: response.status === 401 ? "Authentication required." : "Forbidden.",
      status: response.status,
    });
  }

  const details = await readErrorPayload(response);
  const message =
    parseErrorMessage(details) ?? `API request failed with status ${response.status}.`;

  console.error("fetchFromApi failed", {
    path,
    status: response.status,
    message,
  });

  throw createApiError({
    code: "API_ERROR",
    message,
    status: response.status,
    details,
  });
}
