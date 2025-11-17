import { PageBody, PageHeader } from "@/components/layout";

export default function SkuPage() {
  return (
    <>
      <PageHeader
        title="SKU detail"
        description="Detailed SKU analytics and drill downs will be implemented after the bootstrap phase."
      />
      <PageBody>
        <div className="rounded-xl border bg-background/80 p-6 shadow-sm">
          <p className="text-muted-foreground">
            Expect SKU scorecards, forecast charts, and comparable benchmarks in future drops.
          </p>
        </div>
      </PageBody>
    </>
  );
}
