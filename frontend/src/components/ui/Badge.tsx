const STATUS_COLORS: Record<string, string> = {
  'Settled-Paid': 'bg-green-100 text-green-800',
  'Settled-Payment Pending': 'bg-yellow-100 text-yellow-800',
  'success': 'bg-green-100 text-green-800',
  'failed': 'bg-red-100 text-red-800',
  'in_progress': 'bg-blue-100 text-blue-800',
  'Active': 'bg-green-100 text-green-800',
  'Inactive': 'bg-gray-100 text-gray-500',
}

export default function Badge({ label }: { label: string | null | undefined }) {
  if (!label) return <span className="text-gray-400 text-xs">—</span>
  const color = STATUS_COLORS[label] ?? 'bg-gray-100 text-gray-700'
  return (
    <span className={`inline-flex px-2 py-0.5 text-xs font-medium rounded-full ${color}`}>
      {label}
    </span>
  )
}
