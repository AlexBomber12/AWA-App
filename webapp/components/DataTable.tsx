'use client'

import { useRouter } from 'next/navigation'
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from './ui/table'
import StatBadge from './StatBadge'

export interface DataItem {
  asin: string
  title: string
  roi: number
}

export function DataTable({ data }: { data: DataItem[] }) {
  const router = useRouter()
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>ASIN</TableHead>
          <TableHead>Title</TableHead>
          <TableHead>ROI</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((item) => (
          <TableRow
            key={item.asin}
            className="cursor-pointer"
            onClick={() => router.push(`/sku/${item.asin}`)}
          >
            <TableCell>{item.asin}</TableCell>
            <TableCell>{item.title}</TableCell>
            <TableCell>
              <StatBadge roi={item.roi} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
