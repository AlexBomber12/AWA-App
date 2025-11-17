import { PageBody, PageHeader } from "@/components/layout";

export default function DashboardPage() {
  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Overview cards and operational health checks will land here in PR-UI-1B."
      />
      <PageBody>
        <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
          <p className="text-muted-foreground">
            Configure dashboard cards in future PRs to surface ROI summaries, ingestion errors, and
            SKU health metrics at a glance.
          </p>
        </div>
      </PageBody>
    </>
  );
}
