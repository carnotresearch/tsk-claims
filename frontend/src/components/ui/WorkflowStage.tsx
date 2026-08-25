import type { StatusSnapshotItem } from '../../types'

interface WorkflowStageProps {
  title: string
  titleColor: string
  dotColor: string
  activeBadgeBg: string
  items?: StatusSnapshotItem[]
  onItemClick: (item: StatusSnapshotItem) => void
}

export default function WorkflowStage({
  title,
  titleColor,
  dotColor,
  activeBadgeBg,
  items = [],
  onItemClick,
}: WorkflowStageProps) {
  return (
    <div className="md:col-span-3 bg-slate-50/70 border border-gray-100 rounded-xl p-3">
      <div
        className={`font-bold text-xs ${titleColor} uppercase tracking-wide border-b border-gray-200 pb-1.5 mb-2 flex items-center justify-between`}
      >
        <span>{title}</span>
        <span className={`w-2 h-2 rounded-full ${dotColor}`} />
      </div>
      <div className="space-y-1">
        {items.map((item) => (
          <div
            key={item.status}
            onClick={() => onItemClick(item)}
            className="flex items-center justify-between text-xs py-1 px-2 rounded-lg cursor-pointer hover:bg-indigo-100/70 transition-colors group"
          >
            <span className="text-gray-600 group-hover:text-indigo-700">{item.status}</span>
            <span
              className={`font-semibold tabular-nums px-1.5 py-0.5 rounded text-[11px] ${
                item.count > 0 ? `${activeBadgeBg} text-white shadow-xs` : 'bg-gray-100 text-gray-500'
              }`}
            >
              {item.count}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
