"use client";

import { useEffect, useRef } from "react";

import { type QueryKey, type UseQueryResult } from "@tanstack/react-query";

import type { ApiError } from "@/lib/api/apiError";

import { type UseApiQueryOptions, useApiQuery } from "./useApiQuery";

const DEFAULT_POLLING_INTERVAL_MS = 5000;
const DEFAULT_MAX_DURATION_MS = 5 * 60 * 1000;

export type UsePollingQueryOptions<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = UseApiQueryOptions<TQueryFnData, TError, TData, TQueryKey> & {
  pollingIntervalMs?: number;
  maxDurationMs?: number;
  stopWhen: (data: TData | undefined) => boolean;
};

export function usePollingQuery<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(options: UsePollingQueryOptions<TQueryFnData, TError, TData, TQueryKey>): UseQueryResult<TData, TError> {
  const {
    stopWhen,
    pollingIntervalMs = DEFAULT_POLLING_INTERVAL_MS,
    maxDurationMs = DEFAULT_MAX_DURATION_MS,
    ...queryOptions
  } = options;

  const enabled = queryOptions.enabled ?? true;
  const startTimeRef = useRef<number | null>(null);
  const previousKeyRef = useRef<TQueryKey | null>(null);

  useEffect(() => {
    if (previousKeyRef.current !== options.queryKey) {
      startTimeRef.current = null;
      previousKeyRef.current = options.queryKey;
    }
  }, [options.queryKey]);

  useEffect(() => {
    if (enabled === false) {
      startTimeRef.current = null;
    }
  }, [enabled]);

  return useApiQuery<TQueryFnData, TError, TData, TQueryKey>({
    ...queryOptions,
    refetchInterval: (query) => {
      const data = query.state.data as TData | undefined;

      if (stopWhen(data)) {
        startTimeRef.current = null;
        return false;
      }

      if (enabled === false) {
        return false;
      }

      if (!startTimeRef.current) {
        startTimeRef.current = Date.now();
      }

      if (maxDurationMs && startTimeRef.current) {
        const elapsed = Date.now() - startTimeRef.current;
        if (elapsed >= maxDurationMs) {
          return false;
        }
      }

      return pollingIntervalMs;
    },
  });
}
