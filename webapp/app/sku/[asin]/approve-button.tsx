'use client';

import { useRouter } from 'next/navigation';

export default function ApproveButton({ asin }: { asin: string }) {
  const router = useRouter();
  return (
    <button
      className="px-3 py-1 bg-primary text-primary-foreground rounded"
      onClick={async () => {
        await fetch(`/sku/${asin}/approve`, { method: 'POST' });
        router.back();
      }}
    >
      Approve
    </button>
  );
}
