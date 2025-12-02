"use client";

import { PageBody, PageHeader } from "@/components/layout";
import { ErrorState } from "@/components/data";
import { useReturnsQuery, useReturnsStatsQuery, type ReturnsSort } from "@/lib/api/returnsClient";
import { PermissionGuard } from "@/lib/permissions/client";
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

  const listQuery = useReturnsQuery({
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
    <PermissionGuard
      resource="returns"
      action="view"
      requiredRoles={["viewer", "ops", "admin"]}
      fallback={
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
            <div className="rounded-2xl border border-border bg-muted/30 p-8 text-center">
              <p className="text-base font-semibold">Not authorized</p>
              <p className="mt-1 text-sm text-muted-foreground">You need returns access to view refund trends.</p>
            </div>
          </PageBody>
        </>
      }
    >
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
            rows={listQuery.data?.data ?? listQuery.data?.items ?? []}
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
    </PermissionGuard>
  );
}
