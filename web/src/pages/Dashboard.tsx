import { BarChart, Bar, XAxis, YAxis, LineChart, Line } from 'recharts'
import { useKpi, useRoiByVend, useRoiTrend } from '../lib/api'

interface Kpi {
  name: string
  value: number
}

export default function Dashboard() {
  const { data: kpis = [] } = useKpi()
  const { data: vendors = [] } = useRoiByVend()
  const { data: trend = [] } = useRoiTrend()
  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-3 gap-4">
        {kpis.map((k: Kpi) => (
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
