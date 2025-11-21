"use client";

import { PageBody, PageHeader } from "@/components/layout";
import { ErrorState } from "@/components/data";
import { useReturnsListQuery, useReturnsStatsQuery, type ReturnsSort } from "@/lib/api/returnsClient";
import { useTableState } from "@/lib/tableState";
import {
  RETURNS_TABLE_DEFAULTS,
  parseReturnsSearchParams,
  serializeReturnsSearchParams,
  type ReturnsTableFilters,
} from "@/lib/tableState/returns";

import { ReturnsFilters } from "./ReturnsFilters";
import { ReturnsSummaryTable } from "./ReturnsSummaryTable";
import { ReturnsTable } from "./ReturnsTable";

export function ReturnsPage() {
  const { state, setPage, setPageSize, setSort, setFilters, resetFilters } = useTableState<
    ReturnsSort,
    ReturnsTableFilters
  >({
    defaults: RETURNS_TABLE_DEFAULTS,
    parseFromSearchParams: parseReturnsSearchParams,
    serializeToSearchParams: serializeReturnsSearchParams,
  });

  const appliedFilters = state.filters ?? {};
  const currentSort = state.sort ?? RETURNS_TABLE_DEFAULTS.sort ?? "refund_desc";

  const listQuery = useReturnsListQuery({
    page: state.page,
    pageSize: state.pageSize,
    sort: currentSort,
    filters: appliedFilters,
  });

  const statsQuery = useReturnsStatsQuery(appliedFilters);

  const handleApplyFilters = (filters: ReturnsTableFilters) => {
    setFilters(filters);
  };

  return (
    <>
      <PageHeader
        title="Returns"
        description="Monitor refund volume across ASINs using server-side filters and pagination."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Returns", active: true },
        ]}
      />
      <PageBody>
        <div className="space-y-6">
          <ReturnsSummaryTable
            data={statsQuery.data}
            isLoading={statsQuery.isPending || statsQuery.isRefetching}
            error={statsQuery.error}
            onRetry={() => statsQuery.refetch()}
          />

          <ReturnsFilters
            filters={appliedFilters}
            onApply={handleApplyFilters}
            onReset={resetFilters}
          />

          {listQuery.error ? (
            <ErrorState
              title="Unable to load returns"
              error={listQuery.error}
              onRetry={() => listQuery.refetch()}
            />
          ) : null}

          <ReturnsTable
            rows={listQuery.data?.items ?? []}
            pagination={listQuery.data?.pagination}
            isLoading={listQuery.isPending || listQuery.isRefetching}
            page={state.page}
            pageSize={state.pageSize}
            sort={currentSort}
            onPageChange={setPage}
            onPageSizeChange={setPageSize}
            onSortChange={setSort}
          />
        </div>
      </PageBody>
    </>
  );
}
