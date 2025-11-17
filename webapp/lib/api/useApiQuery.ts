"use client";

import { useEffect } from "react";

import {
  type QueryFunction,
  type QueryKey,
  type UseQueryOptions,
  type UseQueryResult,
  useQuery,
} from "@tanstack/react-query";

const resolveErrorMessage = (value: unknown) => {
  if (!value) {
    return undefined;
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "object" && "message" in value && typeof (value as { message?: unknown }).message === "string") {
    return (value as { message: string }).message;
  }
  return undefined;
};

import type { ApiError } from "@/lib/api/apiError";

export type UseApiQueryOptions<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
> = {
  queryKey: TQueryKey;
  queryFn: QueryFunction<TQueryFnData, TQueryKey>;
  onError?: (error: TError) => void;
} & Omit<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, "queryKey" | "queryFn" | "onError">;

export function useApiQuery<
  TQueryFnData,
  TError = ApiError,
  TData = TQueryFnData,
  TQueryKey extends QueryKey = QueryKey,
>(options: UseApiQueryOptions<TQueryFnData, TError, TData, TQueryKey>): UseQueryResult<TData, TError> {
  type BaseOptions = Omit<UseQueryOptions<TQueryFnData, TError, TData, TQueryKey>, "queryKey" | "queryFn">;
  const { queryKey, queryFn, ...rawRest } = options;
  const { onError, ...restOptions } = rawRest;
  const { staleTime = 30_000, retry = 1, ...rest } = restOptions as BaseOptions;

  const queryResult = useQuery({
    queryKey,
    queryFn,
    staleTime,
    retry,
    ...rest,
  });

  useEffect(() => {
    if (!queryResult.isError || !queryResult.error) {
      return;
    }
    console.error("useApiQuery error", {
      queryKey,
      message: resolveErrorMessage(queryResult.error),
    });
    onError?.(queryResult.error as TError);
  }, [queryResult.isError, queryResult.error, onError, queryKey]);

  return queryResult;
}
