"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  TooltipProps,
  XAxis,
  YAxis,
} from "recharts";

import type { DashboardStatsResponse } from "@/lib/api/statsClient";

type DashboardRoiTrendChartProps = {
  roiTrend: DashboardStatsResponse["roiTrend"];
};

type ChartPoint = {
  label: string;
  month: string;
  roi: number;
  items: number;
};

const formatMonthLabel = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("en-US", { month: "short", year: "numeric" });
};

const buildChartData = (roiTrend: DashboardStatsResponse["roiTrend"]): ChartPoint[] => {
  return (roiTrend.points ?? []).map((point) => ({
    label: formatMonthLabel(point.month),
    month: point.month,
    roi: point.roi_avg,
    items: point.items,
  }));
};

const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }
  const point = payload[0].payload as ChartPoint;
  return (
    <div className="rounded-lg border border-border bg-background/95 px-3 py-2 text-xs shadow">
      <p className="font-medium">{point.label}</p>
      <p className="mt-1 text-muted-foreground">ROI avg: {point.roi.toFixed(1)}%</p>
      <p className="text-muted-foreground">Items: {point.items.toLocaleString()}</p>
    </div>
  );
};

export function DashboardRoiTrendChart({ roiTrend }: DashboardRoiTrendChartProps) {
  const chartData = buildChartData(roiTrend);

  if (chartData.length === 0) {
    return (
      <div className="flex min-h-64 items-center justify-center rounded-2xl border border-dashed border-border bg-background/60 p-8 text-center text-sm text-muted-foreground">
        ROI trend data is unavailable. Try adjusting ROI ingest windows.
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-border bg-background/80 p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">ROI Trend</p>
          <p className="text-lg font-semibold text-foreground">Monthly ROI trajectory</p>
        </div>
        <span className="text-xs uppercase tracking-wide text-muted-foreground">ROI %</span>
      </div>
      <div className="mt-4 h-80 w-full">
        <ResponsiveContainer>
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="roiGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--brand))" stopOpacity={0.4} />
                <stop offset="95%" stopColor="hsl(var(--brand))" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}%`}
              width={60}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="roi"
              stroke="hsl(var(--brand))"
              fill="url(#roiGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
