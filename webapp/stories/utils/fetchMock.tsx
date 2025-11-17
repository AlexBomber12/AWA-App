import { useEffect, type ReactNode } from "react";

type FetchInfo = {
  url: string;
  method: string;
  init?: RequestInit;
};

export type FetchMockHandler = {
  predicate: (info: FetchInfo) => boolean;
  response: (info: FetchInfo) => Response | Promise<Response>;
};

const resolveUrl = (input: RequestInfo | URL): string => {
  if (typeof input === "string") {
    return input;
  }
  if (input instanceof URL) {
    return input.toString();
  }
  return input.url;
};

const resolveMethod = (input: RequestInfo | URL, init?: RequestInit): string => {
  if (typeof Request !== "undefined" && input instanceof Request) {
    return (input.method ?? "GET").toUpperCase();
  }
  return (init?.method ?? "GET").toUpperCase();
};

type FetchMockProps = {
  handlers: FetchMockHandler[];
  children: ReactNode;
};

export function FetchMock({ handlers, children }: FetchMockProps) {
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.fetch !== "function") {
      return undefined;
    }

    const originalFetch = window.fetch.bind(window);

    window.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
      const info: FetchInfo = {
        url: resolveUrl(input),
        method: resolveMethod(input, init),
        init,
      };
      const handler = handlers.find((candidate) => candidate.predicate(info));
      if (handler) {
        return handler.response(info);
      }
      return originalFetch(input, init);
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, [handlers]);

  return <>{children}</>;
}
