"use client";

import { type ComponentProps, useMemo } from "react";

import { ErrorState, SkeletonTable } from "@/components/data";
import { statsClient } from "@/lib/api/statsClient";
import { useApiQuery } from "@/lib/api/useApiQuery";

import { DashboardKpiCard } from "./DashboardKpiCard";
import { DashboardRoiTrendChart } from "./DashboardRoiTrendChart";

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined) {
    return "–";
  }
  return `${value.toFixed(1)}%`;
};

const formatNumber = (value?: number | null) => {
  if (value === null || value === undefined) {
    return "–";
  }
  return value.toLocaleString();
};

type DashboardCard = {
  title: string;
  value: string;
  helperText?: string;
  tooltip?: string;
  deltaLabel?: string;
  severity?: ComponentProps<typeof DashboardKpiCard>["severity"];
};

export function DashboardPageClient() {
  const {
    data: kpi,
    isPending: isKpiLoading,
    error: kpiError,
    refetch: refetchKpi,
  } = useApiQuery({
    queryKey: ["dashboard", "stats", "kpi"],
    queryFn: () => statsClient.getKpi(),
  });

  const {
    data: roiTrend,
    isPending: isRoiLoading,
    error: roiError,
    refetch: refetchRoiTrend,
  } = useApiQuery({
    queryKey: ["dashboard", "stats", "roiTrend"],
    queryFn: () => statsClient.getRoiTrend(),
  });

  const kpiCards: DashboardCard[] = useMemo(() => {
    if (!kpi) {
      return [];
    }

    const roiSeverity = kpi.roi_avg >= 40 ? "positive" : kpi.roi_avg >= 20 ? "neutral" : "warning";
    const roiDelta = roiSeverity === "positive" ? "Healthy" : roiSeverity === "neutral" ? "Watching" : "Action";

    return [
      {
        title: "Average ROI",
        value: formatPercent(kpi.roi_avg),
        helperText: "ROI across the ROI view for the current window.",
        deltaLabel: roiDelta,
        severity: roiSeverity,
        tooltip: "Aggregate ROI percentage computed from the active ROI database view.",
      },
      {
        title: "Products monitored",
        value: formatNumber(kpi.products),
        helperText: "Unique ASINs referenced in the ROI dataset.",
        tooltip: "Count of distinct ASINs returned by the ROI KPI query.",
      },
      {
        title: "Vendors engaged",
        value: formatNumber(kpi.vendors),
        helperText: "Vendors represented across ROI SKUs.",
        tooltip: "Number of distinct vendors contributing to ROI KPIs.",
      },
    ];
  }, [kpi]);

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-base font-semibold text-muted-foreground">Key performance indicators</h2>
        {kpiError ? (
          <ErrorState
            className="mt-4"
            title="Unable to load KPIs"
            error={kpiError}
            onRetry={() => void refetchKpi()}
          />
        ) : isKpiLoading ? (
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {[0, 1, 2].map((item) => (
              <div
                key={`kpi-skeleton-${item}`}
                className="h-32 animate-pulse rounded-2xl border border-border bg-muted/40"
              />
            ))}
          </div>
        ) : (
          <div className="mt-4 grid gap-4 md:grid-cols-3">
            {kpiCards.map((card) => (
              <DashboardKpiCard
                key={card.title}
                title={card.title}
                value={card.value}
                helperText={card.helperText}
                deltaLabel={card.deltaLabel}
                severity={card.severity}
                tooltip={card.tooltip}
              />
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-base font-semibold text-muted-foreground">ROI trajectory</h2>
        {roiError ? (
          <ErrorState
            className="mt-4"
            title="Unable to load ROI trend"
            error={roiError}
            onRetry={() => void refetchRoiTrend()}
          />
        ) : isRoiLoading ? (
          <div className="mt-4">
            <div className="rounded-2xl border border-border bg-background/80 p-6 shadow-sm">
              <SkeletonTable />
            </div>
          </div>
        ) : (
          <div className="mt-4">
            {roiTrend ? <DashboardRoiTrendChart roiTrend={roiTrend} /> : null}
          </div>
        )}
      </section>
    </div>
  );
}
