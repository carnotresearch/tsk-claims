const INR = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

export const formatCurrency = (value: string | number | null | undefined): string => {
  if (value === null || value === undefined || value === '') return '—'
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return '—'
  return INR.format(num)
}

export const formatNumber = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat('en-IN').format(value)
}

export const formatDate = (value: string | null | undefined): string => {
  if (!value) return '—'
  return new Date(value).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

export const formatDays = (value: number | null | undefined): string => {
  if (value === null || value === undefined) return '—'
  return `${value}d`
}
