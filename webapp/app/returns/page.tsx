import { ReturnsQueueTable } from "@/components/features/returns/ReturnsQueueTable";
import { PageBody, PageHeader } from "@/components/layout";

export default function ReturnsPage() {
  return (
    <>
      <PageHeader
        title="Returns"
        description="Returns triage queues surface backlog items from the SP-API feeds."
      />
      <PageBody>
        <ReturnsQueueTable />
      </PageBody>
    </>
  );
}
