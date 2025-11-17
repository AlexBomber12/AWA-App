"use client";

import { useEffect } from "react";

import {
  Button,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui";
import type { ApiError } from "@/lib/api/apiError";
import { fetchFromBff } from "@/lib/api/fetchFromBff";
import { useApiMutation } from "@/lib/api/useApiMutation";

import type { RoiApprovalResponse } from "./types";

type RoiBulkApproveDialogProps = {
  asins: string[];
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => Promise<void> | void;
};

const BULK_APPROVE_ENDPOINT = "/api/bff/roi/bulk-approve";

export function RoiBulkApproveDialog({ asins, isOpen, onOpenChange, onSuccess }: RoiBulkApproveDialogProps) {
  const mutation = useApiMutation<RoiApprovalResponse, ApiError, string[]>({
    mutationFn: async (selectedAsins) => {
      return fetchFromBff<RoiApprovalResponse>(BULK_APPROVE_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ asins: selectedAsins }),
      });
    },
    onSuccess: async () => {
      await onSuccess();
    },
  });

  useEffect(() => {
    if (!isOpen) {
      mutation.reset();
    }
  }, [isOpen, mutation]);

  const sample = asins.slice(0, 5);
  const remaining = Math.max(asins.length - sample.length, 0);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Bulk approve selection</DialogTitle>
          <DialogDescription>
            Approve {asins.length} SKU{asins.length === 1 ? "" : "s"} and lock in the ROI guardrail for this group.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <p className="text-muted-foreground">You are about to approve the following SKUs:</p>
          <ul className="list-disc space-y-1 pl-5">
            {sample.map((asin) => (
              <li key={asin} className="font-mono text-foreground">
                {asin}
              </li>
            ))}
          </ul>
          {remaining > 0 ? (
            <p className="text-muted-foreground">...and {remaining} more.</p>
          ) : null}
          {mutation.isError ? (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {mutation.error?.message ?? "Unable to complete the bulk approval."}
            </p>
          ) : null}
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            onClick={() => mutation.mutate(asins)}
            isLoading={mutation.isPending}
            disabled={asins.length === 0}
          >
            Approve selection
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
