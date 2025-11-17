import { IngestPage as IngestPageClient } from "@/components/features/ingest/IngestPage";
import { PageBody, PageHeader } from "@/components/layout";

export default function IngestPage() {
  return (
    <>
      <PageHeader
        title="Ingest"
        description="Kick off ingest jobs, replay historical files, and monitor Celery progress in real time."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Ingest", active: true },
        ]}
      />
      <PageBody>
        <IngestPageClient />
      </PageBody>
    </>
  );
}
