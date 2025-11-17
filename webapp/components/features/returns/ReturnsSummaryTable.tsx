"use client";

import { DashboardKpiCard } from "@/components/features/dashboard/DashboardKpiCard";
import { ErrorState } from "@/components/data";
import type { ApiError } from "@/lib/api/apiError";
import type { ReturnsSummary } from "@/lib/api/returnsClient";

const formatCurrency = (value: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 2,
  }).format(value);

const formatNumber = (value: number) => value.toLocaleString();

type ReturnsSummaryTableProps = {
  data?: ReturnsSummary;
  isLoading?: boolean;
  error?: ApiError | null;
  onRetry?: () => void;
};

export function ReturnsSummaryTable({ data, isLoading = false, error, onRetry }: ReturnsSummaryTableProps) {
  if (error) {
    return (
      <ErrorState
        title="Unable to load returns summary"
        error={error}
        onRetry={onRetry ? () => onRetry() : undefined}
      />
    );
  }

  const summary: ReturnsSummary = data ?? {
    totalAsins: 0,
    totalUnits: 0,
    totalRefundAmount: 0,
    avgRefundPerUnit: 0,
    topAsin: null,
    topAsinRefundAmount: null,
  };

  const loadingPlaceholder = isLoading && !data;

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <DashboardKpiCard
        title="ASINs with returns"
        value={loadingPlaceholder ? "…" : formatNumber(summary.totalAsins)}
        helperText={summary.topAsin ? `Top ASIN: ${summary.topAsin}` : undefined}
      />
      <DashboardKpiCard
        title="Units returned"
        value={loadingPlaceholder ? "…" : formatNumber(summary.totalUnits)}
        helperText={summary.topAsinRefundAmount ? `Top refund: ${formatCurrency(summary.topAsinRefundAmount)}` : undefined}
      />
      <DashboardKpiCard
        title="Refund amount"
        value={loadingPlaceholder ? "…" : formatCurrency(summary.totalRefundAmount)}
        helperText="Sum of refunds in the selected window"
      />
      <DashboardKpiCard
        title="Avg refund / unit"
        value={loadingPlaceholder ? "…" : formatCurrency(summary.avgRefundPerUnit)}
        helperText="Helps gauge per-unit impact"
      />
    </div>
  );
}
