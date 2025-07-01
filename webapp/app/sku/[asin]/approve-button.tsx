'use client';

import { useRouter } from 'next/navigation';

export default function ApproveButton({ asin }: { asin: string }) {
  const router = useRouter();
  return (
    <button
      className="px-3 py-1 bg-primary text-primary-foreground rounded"
      onClick={async () => {
        const base =
          process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        await fetch(`${base}/sku/${asin}/approve`, { method: 'POST' });
        router.back();
      }}
    >
      Approve
    </button>
  );
}
