import { EmptyState } from "@/components/data";
import { PageBody, PageHeader } from "@/components/layout";
import { Button } from "@/components/ui";

export default function ReturnsPage() {
  return (
    <>
      <PageHeader
        title="Returns"
        description="Return-triage workflows and metrics will be added in subsequent UI milestones."
      />
      <PageBody>
        <EmptyState
          title="No return batches yet"
          description="Once ingestion streams returns data, this workspace will show decision queues and audit history."
          action={
            <Button variant="outline" size="sm">
              Upload preview sample
            </Button>
          }
        />
      </PageBody>
    </>
  );
}
