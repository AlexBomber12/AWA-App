import { useEffect, useState } from 'react'
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
} from '@tanstack/react-table'
import type { ColumnDef } from '@tanstack/react-table'
import { useAuth } from '../context/AuthContext'

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
  const { api } = useAuth()
  const [data, setData] = useState<Row[]>([])
  const [roiMin, setRoiMin] = useState('')
  const [vendor, setVendor] = useState('')
  const [category, setCategory] = useState('')
  const [selected, setSelected] = useState<string[]>([])

  const load = () => {
    api
      .get<Row[]>('/roi-review', {
        params: {
          roi_min: roiMin || undefined,
          vendor: vendor || undefined,
          category: category || undefined,
        },
      })
      .then((r) => setData(r.data))
      .catch(() => setData([]))
  }

  useEffect(load, [roiMin, vendor, category, api])

  const columns: ColumnDef<Row>[] = [
    {
      id: 'select',
      header: '',
      cell: ({ row }) => (
        <input
          type="checkbox"
          checked={selected.includes(row.original.asin)}
          onChange={(e) => {
            setSelected((prev) =>
              e.target.checked
                ? [...prev, row.original.asin]
                : prev.filter((a) => a !== row.original.asin)
            )
          }}
        />
      ),
    },
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
    <div className="space-y-4">
      <div className="flex space-x-2">
        <input
          className="border p-1"
          placeholder="ROI >="
          value={roiMin}
          onChange={(e) => setRoiMin(e.target.value)}
        />
        <input
          className="border p-1"
          placeholder="Vendor"
          value={vendor}
          onChange={(e) => setVendor(e.target.value)}
        />
        <input
          className="border p-1"
          placeholder="Category"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />
        <button
          className="bg-blue-600 text-white px-2 rounded"
          onClick={load}
          type="button"
        >
          Filter
        </button>
        <button
          className="bg-green-600 text-white px-2 rounded"
          onClick={async () => {
            await api.post('/roi-review/approve', { asins: selected })
            setSelected([])
            load()
          }}
          type="button"
        >
          Approve Selected
        </button>
      </div>
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
    </div>
  )
}
