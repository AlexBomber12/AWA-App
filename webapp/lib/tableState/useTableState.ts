"use client";

import {
  type SetStateAction,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

type ComparableValue = string | number | boolean | null | undefined;

export type TableState<TSort, TFilters> = {
  page: number;
  pageSize: number;
  sort?: TSort;
  filters: TFilters;
};

export type TableStateDefaults<TSort, TFilters> = {
  page: number;
  pageSize: number;
  sort?: TSort;
  filters?: TFilters;
};

type UseTableStateOptions<TSort, TFilters> = {
  defaults: TableStateDefaults<TSort, TFilters>;
  parseFromSearchParams: (params: URLSearchParams) => Partial<TableState<TSort, TFilters>>;
  serializeToSearchParams: (state: TableState<TSort, TFilters>) => URLSearchParams;
};

export type UseTableStateResult<TSort, TFilters> = {
  state: TableState<TSort, TFilters>;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;
  setSort: (sort?: TSort) => void;
  setFilters: (filters: SetStateAction<TFilters>) => void;
  resetFilters: () => void;
};

const cloneFilters = <TFilters,>(filters?: TFilters): TFilters => {
  if (filters === undefined) {
    return {} as TFilters;
  }

  if (typeof structuredClone === "function") {
    return structuredClone(filters);
  }

  return JSON.parse(JSON.stringify(filters)) as TFilters;
};

const normalizePositiveInt = (value: number | undefined, fallback: number): number => {
  if (typeof value !== "number") {
    return fallback;
  }
  const parsed = Math.floor(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
};

const toComparable = (value: unknown): ComparableValue => {
  if (typeof value === "object") {
    return JSON.stringify(value ?? null);
  }
  return value as ComparableValue;
};

const isStateEqual = <TSort, TFilters>(
  a: TableState<TSort, TFilters>,
  b: TableState<TSort, TFilters>
): boolean => {
  if (a === b) {
    return true;
  }
  if (a.page !== b.page || a.pageSize !== b.pageSize) {
    return false;
  }
  if (toComparable(a.sort) !== toComparable(b.sort)) {
    return false;
  }
  return toComparable(a.filters) === toComparable(b.filters);
};

export function useTableState<TSort, TFilters>({
  defaults,
  parseFromSearchParams,
  serializeToSearchParams,
}: UseTableStateOptions<TSort, TFilters>): UseTableStateResult<TSort, TFilters> {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const searchParamsString = searchParams.toString();

  const defaultsRef = useRef<TableState<TSort, TFilters>>({
    page: normalizePositiveInt(defaults.page, 1),
    pageSize: normalizePositiveInt(defaults.pageSize, 25),
    sort: defaults.sort,
    filters: cloneFilters(defaults.filters),
  });

  const defaultsHash = useMemo(
    () => JSON.stringify({ page: defaults.page, pageSize: defaults.pageSize, sort: defaults.sort, filters: defaults.filters }),
    [defaults.filters, defaults.page, defaults.pageSize, defaults.sort]
  );

  useEffect(() => {
    defaultsRef.current = {
      page: normalizePositiveInt(defaults.page, 1),
      pageSize: normalizePositiveInt(defaults.pageSize, 25),
      sort: defaults.sort,
      filters: cloneFilters(defaults.filters),
    };
  }, [defaultsHash, defaults.page, defaults.pageSize, defaults.sort, defaults.filters]);

  const mergeWithDefaults = useCallback(
    (partial?: Partial<TableState<TSort, TFilters>>): TableState<TSort, TFilters> => {
      const baseline = defaultsRef.current;
      return {
        page: normalizePositiveInt(partial?.page, baseline.page),
        pageSize: normalizePositiveInt(partial?.pageSize, baseline.pageSize),
        sort: partial?.sort ?? baseline.sort,
        filters: partial?.filters ? partial.filters : cloneFilters(baseline.filters),
      };
    },
    []
  );

  const computeStateFromSearchParams = useCallback(() => {
    const parsed = parseFromSearchParams(searchParams);
    return mergeWithDefaults(parsed);
  }, [mergeWithDefaults, parseFromSearchParams, searchParams]);

  const [state, setState] = useState<TableState<TSort, TFilters>>(() => computeStateFromSearchParams());

  const lastSyncedQueryRef = useRef<string>(searchParamsString);
  const lastSyncedPathRef = useRef<string | null>(pathname);

  const syncUrl = useCallback(
    (nextState: TableState<TSort, TFilters>) => {
      const params = serializeToSearchParams(nextState);
      const query = params.toString();

      const alreadySynced =
        query === lastSyncedQueryRef.current && pathname === lastSyncedPathRef.current;

      if (alreadySynced) {
        return;
      }

      lastSyncedQueryRef.current = query;
      lastSyncedPathRef.current = pathname;

      const nextUrl = query ? `${pathname}?${query}` : pathname;
      void router.replace(nextUrl, { scroll: false });
    },
    [pathname, router, serializeToSearchParams]
  );

  useEffect(() => {
    const derivedState = computeStateFromSearchParams();
    setState((current) => (isStateEqual(current, derivedState) ? current : derivedState));
    lastSyncedQueryRef.current = searchParamsString;
    lastSyncedPathRef.current = pathname;
  }, [computeStateFromSearchParams, pathname, searchParamsString]);

  const updateState = useCallback(
    (updater: (current: TableState<TSort, TFilters>) => TableState<TSort, TFilters>) => {
      setState((current) => {
        const next = updater(current);
        if (!isStateEqual(current, next)) {
          syncUrl(next);
          return next;
        }
        return current;
      });
    },
    [syncUrl]
  );

  const setPage = useCallback(
    (page: number) => {
      updateState((current) => {
        const normalized = normalizePositiveInt(page, current.page);
        if (normalized === current.page) {
          return current;
        }
        return { ...current, page: normalized };
      });
    },
    [updateState]
  );

  const setPageSize = useCallback(
    (pageSize: number) => {
      updateState((current) => {
        const normalized = normalizePositiveInt(pageSize, defaultsRef.current.pageSize);
        if (normalized === current.pageSize && current.page === 1) {
          return current;
        }
        return { ...current, pageSize: normalized, page: 1 };
      });
    },
    [updateState]
  );

  const setSort = useCallback(
    (sort?: TSort) => {
      updateState((current) => {
        if (toComparable(current.sort) === toComparable(sort)) {
          return current;
        }
        return { ...current, sort, page: 1 };
      });
    },
    [updateState]
  );

  const setFilters = useCallback(
    (filters: SetStateAction<TFilters>) => {
      updateState((current) => {
        const nextFilters =
          typeof filters === "function"
            ? (filters as (prev: TFilters) => TFilters)(current.filters)
            : filters;
        if (toComparable(current.filters) === toComparable(nextFilters)) {
          return current;
        }
        return { ...current, filters: nextFilters, page: 1 };
      });
    },
    [updateState]
  );

  const resetFilters = useCallback(() => {
    setFilters(cloneFilters(defaultsRef.current.filters));
  }, [setFilters]);

  return {
    state,
    setPage,
    setPageSize,
    setSort,
    setFilters,
    resetFilters,
  };
}
