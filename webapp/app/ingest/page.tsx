import { PageBody, PageHeader } from "@/components/layout";

export default function IngestPage() {
  return (
    <>
      <PageHeader
        title="Ingest"
        description="Data ingestion monitors and replay tooling will surface in this area."
      />
      <PageBody>
        <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
          <p className="text-muted-foreground">
            Monitor AWS pipelines, replay failed batches, and trace SKU impacts once integration
            specs are complete.
          </p>
        </div>
      </PageBody>
    </>
  );
}
