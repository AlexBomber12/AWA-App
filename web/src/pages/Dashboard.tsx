import { useEffect, useState } from 'react'
import { fetchJSON } from '../api'
import { BarChart, Bar, XAxis, YAxis, LineChart, Line } from 'recharts'

interface KPI {
  name: string
  value: number
}
interface VendorROI { vendor: string; roi: number }
interface TrendPoint { date: string; roi: number }

export default function Dashboard() {
  const token = localStorage.getItem('token') || ''
  const [kpis, setKpis] = useState<KPI[]>([])
  const [vendors, setVendors] = useState<VendorROI[]>([])
  const [trend, setTrend] = useState<TrendPoint[]>([])
  useEffect(() => {
    fetchJSON<KPI[]>('/stats/kpi', token).then(setKpis).catch(() => setKpis([]))
    fetchJSON<VendorROI[]>('/stats/roi_by_vendor', token)
      .then(setVendors)
      .catch(() => setVendors([]))
    fetchJSON<TrendPoint[]>('/stats/roi_trend', token)
      .then(setTrend)
      .catch(() => setTrend([]))
  }, [token])
  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {kpis.map((k) => (
          <div key={k.name} className="p-4 bg-white rounded shadow">
            <div className="text-sm text-gray-500">{k.name}</div>
            <div className="text-2xl font-bold">{k.value}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        <BarChart width={400} height={200} data={vendors}>
          <XAxis dataKey="vendor" />
          <YAxis />
          <Bar dataKey="roi" fill="#8884d8" />
        </BarChart>
        <LineChart width={400} height={200} data={trend}>
          <XAxis dataKey="date" />
          <YAxis />
          <Line type="monotone" dataKey="roi" stroke="#82ca9d" />
        </LineChart>
      </div>
    </div>
  )
}
