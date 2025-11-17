"use client";

import Link from "next/link";

import { ErrorState } from "@/components/data";
import { type SkuDetail, useSkuDetailQuery } from "@/lib/api/skuClient";

import { SkuCard } from "./SkuCard";
import { SkuPriceHistoryChart } from "./SkuPriceHistoryChart";

type SkuPageProps = {
  asin: string;
  from?: "roi" | "returns" | null;
  initialData?: SkuDetail;
  fetchEnabled?: boolean;
};

const backlinkMap: Record<NonNullable<SkuPageProps["from"]>, { label: string; href: string }> = {
  roi: { label: "Back to ROI", href: "/roi" },
  returns: { label: "Back to Returns", href: "/returns" },
};

const backLinkClassName =
  "inline-flex items-center justify-center rounded-md border border-border bg-transparent px-3 py-1 text-sm font-medium text-brand transition hover:bg-muted/70";

const SkuPageSkeleton = () => (
  <div data-testid="sku-page-skeleton" className="space-y-4">
    <div className="h-64 animate-pulse rounded-2xl border border-border bg-muted/40" />
    <div className="h-80 animate-pulse rounded-2xl border border-border bg-muted/20" />
  </div>
);

export function SkuPage({ asin, from = null, initialData, fetchEnabled }: SkuPageProps) {
  const queryOptions: Parameters<typeof useSkuDetailQuery>[1] =
    fetchEnabled === undefined ? { initialData } : { initialData, enabled: fetchEnabled };
  const {
    data,
    error,
    isPending,
    refetch,
  } = useSkuDetailQuery(asin, queryOptions);

  const backlink = from ? backlinkMap[from] : null;

  const backlinkNode = backlink ? (
    <div className="flex justify-end">
      <Link className={backLinkClassName} href={backlink.href} prefetch={false}>
        {backlink.label}
      </Link>
    </div>
  ) : null;

  if (!asin) {
    return (
      <div className="space-y-6">
        {backlinkNode}
        <ErrorState
          title="Missing SKU identifier"
          message="Select a SKU from ROI or Returns to open its detail view."
        />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        {backlinkNode}
        <ErrorState
          title="Unable to load SKU detail"
          error={error}
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  if (isPending || !data) {
    return (
      <div className="space-y-6">
        {backlinkNode}
        <SkuPageSkeleton />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {backlinkNode}
      <SkuCard detail={data} />
      <SkuPriceHistoryChart history={data.chartData} />
    </div>
  );
}
