import type { ReactNode } from 'react'

interface Props {
  label: string
  value: string
  sub?: string
  accent?: string
  icon?: ReactNode
}

export default function KpiCard({ label, value, sub, accent = 'border-indigo-500', icon }: Props) {
  return (
    <div className={`card border-l-4 ${accent} flex items-start justify-between`}>
      <div>
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
        <p className="mt-1 text-2xl font-bold text-gray-900 tracking-tight">{value}</p>
        {sub && <p className="mt-0.5 text-xs text-gray-400">{sub}</p>}
      </div>
      {icon && <div className="text-gray-300 mt-1">{icon}</div>}
    </div>
  )
}
