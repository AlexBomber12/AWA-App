import { PageBody, PageHeader } from "@/components/layout";

export default function InboxPage() {
  return (
    <>
      <PageHeader
        title="Inbox"
        description="The Inbox combines alerts and workflow assignments; stubs exist here until PR-UI-1C."
      />
      <PageBody>
        <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
          <p className="text-muted-foreground">
            Alert triage, SLA countdowns, and collaboration history will plug in here once the
            workflow orchestration service lands.
          </p>
        </div>
      </PageBody>
    </>
  );
}
