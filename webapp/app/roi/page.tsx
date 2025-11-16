import { RoiActions } from "./RoiActions";

export default function RoiPage() {
  return (
    <section className="space-y-4">
      <div className="space-y-3">
        <h2 className="text-3xl font-semibold tracking-tight">ROI review</h2>
        <p className="text-muted-foreground">
          ROI scenarios and guardrails will plug into this workspace in upcoming releases.
        </p>
      </div>
      <RoiActions />
    </section>
  );
}
