"use client";

import { Button } from "@/components/ui/button";
import { PermissionGuard } from "@/lib/permissions";

export function RoiActions() {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <PermissionGuard
        resource="roi"
        action="approve"
        fallback={
          <p className="text-sm text-muted-foreground">
            Ops access is required to run ROI approvals.
          </p>
        }
      >
        <Button>Approve pending ROI batch</Button>
      </PermissionGuard>
    </div>
  );
}
