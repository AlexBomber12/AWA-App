import { useEffect, useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import type { ColumnDef } from '@tanstack/react-table'
import { fetchJSON } from '../api'

interface Row {
  asin: string
  title: string
  vendor_id: number
  cost: number
  freight: number
  fees: number
  roi_pct: number
}

export default function RoiReview() {
  const token = localStorage.getItem('token') || ''
  const [data, setData] = useState<Row[]>([])
  useEffect(() => {
    fetchJSON<Row[]>('/roi-review', token).then(setData).catch(() => setData([]))
  }, [token])

  const columns: ColumnDef<Row>[] = [
    { accessorKey: 'asin', header: 'ASIN' },
    { accessorKey: 'title', header: 'Title' },
    { accessorKey: 'vendor_id', header: 'Vendor' },
    { accessorKey: 'cost', header: 'Cost' },
    { accessorKey: 'freight', header: 'Freight' },
    { accessorKey: 'fees', header: 'Fees' },
    { accessorKey: 'roi_pct', header: 'ROI %' },
  ]

  const table = useReactTable({ data, columns, getCoreRowModel: getCoreRowModel() })

  return (
    <table className="min-w-full border">
      <thead>
        {table.getHeaderGroups().map((hg) => (
          <tr key={hg.id}>
            {hg.headers.map((h) => (
              <th key={h.id} className="border p-2 text-left">
                {flexRender(h.column.columnDef.header, h.getContext())}
              </th>
            ))}
          </tr>
        ))}
      </thead>
      <tbody>
        {table.getRowModel().rows.map((row) => (
          <tr key={row.id} className="border-t">
            {row.getVisibleCells().map((cell) => (
              <td key={cell.id} className="border p-2">
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
