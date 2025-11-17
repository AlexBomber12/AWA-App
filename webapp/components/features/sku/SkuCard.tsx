import type { SkuDetail } from "@/lib/api/skuClient";

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

const formatCurrency = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "–";
  }
  return currencyFormatter.format(value);
};

const formatPercent = (value?: number | null) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "–";
  }
  return `${value.toFixed(1)}%`;
};

const getLatestPrice = (history: SkuDetail["chartData"]): number | null => {
  if (!history || history.length === 0) {
    return null;
  }
  return history[history.length - 1]?.price ?? null;
};

const getPriceDelta = (history: SkuDetail["chartData"]) => {
  if (!history || history.length < 2) {
    return null;
  }

  const first = history[0]?.price;
  const last = history[history.length - 1]?.price;

  if (first === undefined || last === undefined || first === 0) {
    return null;
  }

  const absolute = last - first;
  const percent = (absolute / first) * 100;
  return { absolute, percent };
};

const badgeClass = (variant: "positive" | "warning" | "neutral") => {
  switch (variant) {
    case "positive":
      return "border-emerald-300 bg-emerald-50 text-emerald-800";
    case "warning":
      return "border-amber-300 bg-amber-50 text-amber-800";
    default:
      return "border-border bg-muted/40 text-muted-foreground";
  }
};

const resolveRoiBadge = (roi: number) => {
  if (roi >= 40) {
    return { label: "High ROI", variant: "positive" as const };
  }
  if (roi >= 20) {
    return { label: "ROI watch", variant: "neutral" as const };
  }
  return { label: "Action required", variant: "warning" as const };
};

const describeDelta = (delta: { absolute: number; percent: number }) => {
  const absoluteLabel = `${delta.absolute >= 0 ? "+" : ""}${formatCurrency(delta.absolute)}`;
  const percentLabel = `${delta.percent >= 0 ? "+" : ""}${delta.percent.toFixed(1)}%`;
  return `${absoluteLabel} (${percentLabel})`;
};

type SkuCardProps = {
  detail: SkuDetail;
};

export function SkuCard({ detail }: SkuCardProps) {
  const latestPrice = getLatestPrice(detail.chartData);
  const priceDelta = getPriceDelta(detail.chartData);
  const roiBadge = resolveRoiBadge(detail.roi);
  const estimatedMargin =
    latestPrice !== null && latestPrice !== undefined ? latestPrice - detail.fees : null;

  return (
    <section className="rounded-2xl border border-border bg-background/80 p-6 shadow-sm">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            SKU snapshot
          </p>
          <h2 className="mt-1 text-2xl font-semibold leading-tight text-foreground">{detail.title}</h2>
          <p className="mt-1 text-sm text-muted-foreground">ASIN · {detail.asin}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span
            className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold ${badgeClass(
              roiBadge.variant
            )}`}
          >
            {roiBadge.label}
          </span>
          {priceDelta ? (
            <span className="inline-flex items-center rounded-full border border-sky-300 bg-sky-50 px-3 py-1 text-xs font-semibold text-sky-800">
              Price vs first capture {describeDelta(priceDelta)}
            </span>
          ) : null}
        </div>
      </div>

      <dl className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Return on investment
          </dt>
          <dd className="mt-2 text-3xl font-semibold text-foreground">{formatPercent(detail.roi)}</dd>
          <p className="mt-1 text-sm text-muted-foreground">Rolling ROI for the SKU.</p>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Latest buy box price
          </dt>
          <dd className="mt-2 text-3xl font-semibold text-foreground">{formatCurrency(latestPrice)}</dd>
          <p className="mt-1 text-sm text-muted-foreground">Based on the latest history tick.</p>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Fees / COGS
          </dt>
          <dd className="mt-2 text-3xl font-semibold text-foreground">{formatCurrency(detail.fees)}</dd>
          <p className="mt-1 text-sm text-muted-foreground">Inbound, fulfillment, or landed fees.</p>
        </div>
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Estimated margin
          </dt>
          <dd className="mt-2 text-3xl font-semibold text-foreground">{formatCurrency(estimatedMargin)}</dd>
          <p className="mt-1 text-sm text-muted-foreground">Latest price minus fees.</p>
        </div>
      </dl>
    </section>
  );
}
