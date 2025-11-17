"use client";

import {
  type UseMutationOptions,
  type UseMutationResult,
  useMutation,
} from "@tanstack/react-query";

import type { ApiError } from "@/lib/api/apiError";

export function useApiMutation<
  TData = unknown,
  TError = ApiError,
  TVariables = void,
  TContext = unknown,
>(
  options: UseMutationOptions<TData, TError, TVariables, TContext>
): UseMutationResult<TData, TError, TVariables, TContext> {
  const { onError, retry = 0, ...rest } = options;

  return useMutation({
    retry,
    ...rest,
    onError: (error, variables, context, mutation) => {
      console.error("useApiMutation error", {
        message: (error as ApiError | Error)?.message,
      });
      onError?.(error, variables, context, mutation);
    },
  });
}
