import type { ReactNode } from 'react'
import { ArrowUpRight } from 'lucide-react'

interface Props {
  label: string
  value: string
  sub?: string
  icon?: ReactNode
  badge?: string
  badgeColor?: string
  onClick?: () => void
}

export default function KpiCard({
  label,
  value,
  sub,
  icon,
  badge,
  badgeColor = 'bg-gray-100 text-gray-700',
  onClick,
}: Props) {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-gray-200/80 p-4 shadow-2xs transition-all duration-200 ${
        onClick
          ? 'cursor-pointer hover:shadow-md hover:border-indigo-300 hover:-translate-y-0.5 active:translate-y-0 select-none group'
          : ''
      } flex flex-col justify-between`}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider truncate">
          {label}
        </span>
        {icon && (
          <div className="p-2 rounded-lg bg-slate-50 text-gray-500 group-hover:bg-indigo-50 group-hover:text-indigo-600 transition-colors shrink-0">
            {icon}
          </div>
        )}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xl sm:text-2xl font-black tracking-tight text-gray-900 tabular-nums whitespace-nowrap group-hover:text-indigo-600 transition-colors">
            {value}
          </p>
          {sub && (
            <p className="text-[11px] text-gray-500 font-medium mt-0.5 truncate">
              {sub}
            </p>
          )}
        </div>

        {badge ? (
          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${badgeColor} shrink-0`}>
            {badge}
          </span>
        ) : onClick ? (
          <div className="p-1 rounded-full text-gray-300 group-hover:text-indigo-500 group-hover:bg-indigo-50 transition-all opacity-0 group-hover:opacity-100 shrink-0">
            <ArrowUpRight size={14} />
          </div>
        ) : null}
      </div>
    </div>
  )
}
