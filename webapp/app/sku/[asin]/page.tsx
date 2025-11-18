import { SkuPage } from "@/components/features/sku/SkuPage";
import { PageBody, PageHeader, type BreadcrumbItem } from "@/components/layout";
import { getServerAuthSession } from "@/lib/auth";
import { can, getUserRolesFromSession } from "@/lib/permissions/server";

const normalizeSource = (value?: string | string[] | null): "roi" | "returns" | null => {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.toLowerCase();
  return normalized === "roi" || normalized === "returns" ? normalized : null;
};

type PageProps = {
  params: { asin: string };
  searchParams?: Record<string, string | string[] | undefined>;
};

export default async function SkuDetailPage({ params, searchParams }: PageProps) {
  const asinParam = decodeURIComponent(params.asin);
  const displayAsin = asinParam.toUpperCase();
  const from = normalizeSource(searchParams?.from);

  const session = await getServerAuthSession();
  const roles = getUserRolesFromSession(session);
  const canViewSku = can({ resource: "sku", action: "view", roles });

  const fromBreadcrumb: BreadcrumbItem | null =
    from === "roi" ? { label: "ROI", href: "/roi" } : from === "returns" ? { label: "Returns", href: "/returns" } : null;

  const breadcrumbs: BreadcrumbItem[] = [
    { label: "Dashboard", href: "/dashboard" },
    ...(fromBreadcrumb ? [fromBreadcrumb] : []),
    { label: `SKU ${displayAsin}`, active: true },
  ];

  const headerDescription =
    from === "roi"
      ? "Context from the ROI review pipeline."
      : from === "returns"
        ? "Context from the Returns triage workspace."
        : "Drill into SKU ROI and price telemetry.";

  if (!canViewSku) {
    return (
      <>
        <PageHeader
          title={`SKU ${displayAsin}`}
          description="You do not have access to view SKU analytics."
          breadcrumbs={breadcrumbs}
        />
        <PageBody>
          <div className="rounded-2xl border border-border bg-muted/30 p-8 text-center">
            <p className="text-base font-semibold">Access denied</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Ask an administrator to grant the sku:view permission to view this page.
            </p>
          </div>
        </PageBody>
      </>
    );
  }

  return (
    <>
      <PageHeader
        title={`SKU ${displayAsin}`}
        description={headerDescription}
        breadcrumbs={breadcrumbs}
      />
      <PageBody>
        <SkuPage asin={asinParam} from={from} />
      </PageBody>
    </>
  );
}
