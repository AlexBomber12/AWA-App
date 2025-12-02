"use client";

import { Suspense, type ReactNode, useCallback, useState } from "react";

import { PageBody, PageHeader } from "@/components/layout";
import { usePermissions } from "@/lib/permissions/client";
import { PermissionGuard } from "@/lib/permissions/client";

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

  const unauthorized = (
    <>
      <PageHeader
        title="ROI review"
        description="Review ROI guardrail breaches, adjust filters, and bulk approve the SKUs that meet current thresholds."
        breadcrumbs={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "ROI", active: true },
        ]}
      />
      <PageBody>
        <div className="rounded-2xl border border-border bg-muted/30 p-8 text-center">
          <p className="text-base font-semibold">Not authorized</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Ask an administrator to grant ROI access before reviewing guardrail decisions.
          </p>
        </div>
      </PageBody>
    </>
  );

  return (
    <PermissionGuard resource="roi" action="view" requiredRoles={["viewer", "ops", "admin"]} fallback={unauthorized}>
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
    </PermissionGuard>
  );
}
