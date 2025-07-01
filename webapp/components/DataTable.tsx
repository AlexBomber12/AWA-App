'use client';

import { useRouter } from 'next/navigation';

export interface DataItem {
  asin: string;
  title: string;
  roi: number;
}

export function DataTable({ data }: { data: DataItem[] }) {
  const router = useRouter();
  return (
    <table className="w-full text-sm">
      <thead>
        <tr>
          <th className="text-left p-2">ASIN</th>
          <th className="text-left p-2">Title</th>
          <th className="text-left p-2">ROI</th>
        </tr>
      </thead>
      <tbody>
        {data.map((item) => (
          <tr
            key={item.asin}
            className="cursor-pointer hover:bg-accent"
            onClick={() => router.push(`/sku/${item.asin}`)}
          >
            <td className="p-2">{item.asin}</td>
            <td className="p-2">{item.title}</td>
            <td className="p-2">{item.roi}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
