interface StatBadgeProps {
  roi: number
}

export default function StatBadge({ roi }: StatBadgeProps) {
  const color = roi >= 0 ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
  return (
    <span className={`rounded-md px-2 py-1 text-xs font-medium ${color}`}>{roi}%</span>
  )
}
