import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import { getClaims } from '../api/claims'
import { formatCurrency, formatDate } from '../lib/format'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

const STATUS_OPTIONS = [
  'Settled-Paid',
  'Settled-Payment Pending',
  'Query Raised',
  'Denied',
  'In Progress',
]

const PAYER_OPTIONS = ['Insurer', 'TPA', 'Govt', 'Self-funded']
const AGEING_OPTIONS = ['0-30', '31-60', '61-90', '90+']

export default function Claims() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [payerType, setPayerType] = useState('')
  const [ageingBucket, setAgeingBucket] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['claims', page, search, status, payerType, ageingBucket, dateFrom, dateTo],
    queryFn: () => getClaims({
      page,
      page_size: 20,
      search: search || undefined,
      status: status || undefined,
      payer_type: payerType || undefined,
      ageing_bucket: ageingBucket || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    placeholderData: (prev) => prev,
  })

  const resetFilters = () => {
    setSearch(''); setStatus(''); setPayerType('')
    setAgeingBucket(''); setDateFrom(''); setDateTo(''); setPage(1)
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="card p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3">
          <div className="relative xl:col-span-2">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              className="input pl-8"
              placeholder="Search patient or HSK ref…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1) }}
            />
          </div>
          <select className="input" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1) }}>
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select className="input" value={payerType} onChange={(e) => { setPayerType(e.target.value); setPage(1) }}>
            <option value="">All Payers</option>
            {PAYER_OPTIONS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <select className="input" value={ageingBucket} onChange={(e) => { setAgeingBucket(e.target.value); setPage(1) }}>
            <option value="">All Ageing</option>
            {AGEING_OPTIONS.map(a => <option key={a} value={a}>{a} days</option>)}
          </select>
          <button className="btn-secondary text-xs" onClick={resetFilters}>Reset</button>
        </div>
        <div className="grid grid-cols-2 gap-3 mt-3 max-w-sm">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Admission From</label>
            <input type="date" className="input text-sm" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(1) }} />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Admission To</label>
            <input type="date" className="input text-sm" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(1) }} />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            {data ? `${data.total.toLocaleString('en-IN')} claims` : '—'}
          </p>
        </div>
        {isLoading ? <Spinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  {['HSK Ref', 'Patient', 'Admission', 'Insurer', 'Billed', 'Approved', 'Paid', 'Ageing', 'Status'].map(h => (
                    <th key={h} className="text-left py-2.5 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data?.items.map(c => (
                  <tr
                    key={c.id}
                    className="hover:bg-indigo-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/claims/${c.id}`)}
                  >
                    <td className="py-2.5 px-3 font-mono text-xs text-gray-600">{c.hsk_ref_id ?? '—'}</td>
                    <td className="py-2.5 px-3 font-medium text-gray-800 max-w-[140px] truncate">{c.patient_name ?? '—'}</td>
                    <td className="py-2.5 px-3 text-gray-500 whitespace-nowrap text-xs">{formatDate(c.date_admission)}</td>
                    <td className="py-2.5 px-3 text-gray-600 text-xs">{c.insurer_name ?? c.payer_type ?? '—'}</td>
                    <td className="py-2.5 px-3 tabular-nums text-gray-700 text-xs">{formatCurrency(c.final_claimed_amt)}</td>
                    <td className="py-2.5 px-3 tabular-nums text-gray-700 text-xs">{formatCurrency(c.final_bill_approved_amt)}</td>
                    <td className="py-2.5 px-3 tabular-nums text-gray-700 text-xs">{formatCurrency(c.payment_received_amt)}</td>
                    <td className="py-2.5 px-3 text-xs text-gray-500">{c.ageing_bucket ?? '—'}</td>
                    <td className="py-2.5 px-3"><Badge label={c.final_claim_status} /></td>
                  </tr>
                ))}
                {data?.items.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-12 text-center text-gray-400 text-sm">No claims match the current filters</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-100 flex items-center justify-between">
            <p className="text-xs text-gray-500">Page {data.page} of {data.pages}</p>
            <div className="flex gap-1">
              <button
                className="btn-secondary py-1 px-2 text-xs disabled:opacity-40"
                onClick={() => setPage(p => p - 1)}
                disabled={page === 1}
              >
                <ChevronLeft size={14} />
              </button>
              <button
                className="btn-secondary py-1 px-2 text-xs disabled:opacity-40"
                onClick={() => setPage(p => p + 1)}
                disabled={page >= data.pages}
              >
                <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
