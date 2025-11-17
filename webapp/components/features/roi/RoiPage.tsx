"use client";

import { Suspense, type ReactNode, useCallback, useState } from "react";

import { PageBody, PageHeader } from "@/components/layout";
import { usePermissions } from "@/lib/permissions";

import { RoiTableContainer } from "./RoiTableContainer";

export function RoiPage() {
  const { can } = usePermissions();
  const [actions, setActions] = useState<ReactNode | null>(null);
  const canApprove = can({ resource: "roi", action: "approve" });

  const handleActionsChange = useCallback(
    (node: ReactNode | null) => {
      setActions(canApprove ? node : null);
    },
    [canApprove]
  );

  return (
    <>
      <PageHeader
        title="ROI review"
        description="Review ROI guardrail breaches, adjust filters, and bulk approve the SKUs that meet current thresholds."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "ROI", active: true },
        ]}
        actions={actions}
      />
      <PageBody>
        <Suspense fallback={<div className="rounded-xl border border-border bg-background/80 p-6 shadow-sm">Loading ROI review…</div>}>
          <RoiTableContainer canApprove={canApprove} onActionsChange={handleActionsChange} />
        </Suspense>
      </PageBody>
    </>
  );
}
