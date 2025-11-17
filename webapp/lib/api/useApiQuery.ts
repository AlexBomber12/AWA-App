"use client";

import {
  type QueryFunction,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
  useQuery,
} from "@tanstack/react-query";

import type { ApiError } from "@/lib/api/apiError";

type UseApiQueryOptions<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = {
  queryKey: TQueryKey;
  queryFn: QueryFunction<TQueryFnData, TQueryKey>;
} & Omit<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, "queryKey" | "queryFn">;

export function useApiQuery<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(options: UseApiQueryOptions<TQueryFnData, TError, TData, TQueryKey>): UseQueryResult<TData, TError> {
  const { queryKey, queryFn, onError, staleTime = 30_000, retry = 1, ...rest } = options;

  return useQuery({
    queryKey,
    queryFn,
    staleTime,
    retry,
    ...rest,
    onError: (error) => {
      console.error("useApiQuery error", {
        queryKey,
        message: (error as ApiError | Error)?.message,
      });
      onError?.(error);
    },
  });
}
