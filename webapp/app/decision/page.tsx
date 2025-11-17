import { PageBody, PageHeader } from "@/components/layout";

export default function DecisionPage() {
  return (
    <>
      <PageHeader
        title="Decision Engine"
        description="Decision Engine modeling and approvals connect here once the ROI/Virtual Buyer specs ship."
      />
      <PageBody>
        <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
          <p className="text-muted-foreground">
            Future iterations will plug in guardrail tuning, workflow queues, and what-if models to
            keep operator approvals auditable.
          </p>
        </div>
      </PageBody>
    </>
  );
}
