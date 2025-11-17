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

import type { SkuDetail } from "@/lib/api/skuClient";

type SkuPriceHistoryChartProps = {
  history: SkuDetail["chartData"];
};

type HistoryPoint = {
  date: string;
  label: string;
  price: number;
};

const formatDateLabel = (value: string) => {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
};

const buildChartData = (history: SkuDetail["chartData"]): HistoryPoint[] => {
  return (history ?? []).map((point) => ({
    date: point.date,
    label: formatDateLabel(point.date),
    price: point.price,
  }));
};

type PriceTooltipProps = TooltipProps<number, string> & {
  payload?: Array<{ payload: HistoryPoint }>;
};

const PriceTooltip = ({ active, payload }: PriceTooltipProps) => {
  if (!active || !payload || payload.length === 0) {
    return null;
  }
  const point = payload[0]?.payload;
  if (!point) {
    return null;
  }
  return (
    <div className="rounded-lg border border-border bg-background/95 px-3 py-2 text-xs shadow">
      <p className="font-semibold">{point.label}</p>
      <p className="mt-1 text-muted-foreground">${point.price.toFixed(2)}</p>
    </div>
  );
};

export function SkuPriceHistoryChart({ history }: SkuPriceHistoryChartProps) {
  const chartData = buildChartData(history);

  if (chartData.length === 0) {
    return (
      <section className="rounded-2xl border border-dashed border-border bg-background/70 p-6 text-center text-sm text-muted-foreground">
        Price history is not available yet. Once FastAPI emits chart data, the ROI + price trend will render here.
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-border bg-background/80 p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-muted-foreground">Price & ROI history</p>
          <p className="text-lg font-semibold text-foreground">Buy box trajectory</p>
        </div>
        <span className="text-xs uppercase tracking-wide text-muted-foreground">USD</span>
      </div>
      <div className="mt-4 h-80 w-full">
        <ResponsiveContainer>
          <AreaChart data={chartData} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="skuPriceGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--brand))" stopOpacity={0.4} />
                <stop offset="95%" stopColor="hsl(var(--brand))" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis dataKey="label" tickLine={false} axisLine={false} minTickGap={24} />
            <YAxis
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
              width={70}
            />
            <Tooltip content={<PriceTooltip />} />
            <Area
              type="monotone"
              dataKey="price"
              stroke="hsl(var(--brand))"
              fill="url(#skuPriceGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
