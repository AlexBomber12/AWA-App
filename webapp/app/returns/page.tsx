import { Suspense } from "react";

import { ReturnsPage as ReturnsPageContent } from "@/components/features/returns/ReturnsPage";

export const metadata = {
  title: "Returns | AWA",
};

export default function ReturnsRoutePage() {
  return (
    <Suspense fallback={<div className="rounded-xl border border-border bg-background/80 p-6 shadow-sm">Loading returns…</div>}>
      <ReturnsPageContent />
    </Suspense>
  );
}
