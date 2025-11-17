import { RoiReviewTable } from "@/components/features/roi/RoiReviewTable";
import { PageBody, PageHeader } from "@/components/layout";

import { RoiActions } from "./RoiActions";

export default function RoiPage() {
  return (
    <>
      <PageHeader
        title="ROI review"
        description="ROI scenarios and guardrails will plug into this workspace in upcoming releases."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "ROI", active: true },
        ]}
        actions={<RoiActions />}
      />
      <PageBody>
        <RoiReviewTable />
      </PageBody>
    </>
  );
}
