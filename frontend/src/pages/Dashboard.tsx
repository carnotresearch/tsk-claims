import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import KpiCard from '../components/ui/KpiCard'
import Spinner from '../components/ui/Spinner'
import { getKPIs, getTAT, getAgeing, getPayerPerformance, getMonthly, getStatusBreakdown } from '../api/analytics'
import { formatCurrency, formatNumber, formatDays } from '../lib/format'
import { TrendingUp, Clock, AlertCircle, CheckCircle, DollarSign, FileText } from 'lucide-react'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

const fmt = (v: string | number | undefined) => {
  if (!v) return 0
  return typeof v === 'string' ? parseFloat(v) : v
}

export default function Dashboard() {
  const kpisQ = useQuery({ queryKey: ['kpis'], queryFn: () => getKPIs() })
  const tatQ = useQuery({ queryKey: ['tat'], queryFn: () => getTAT() })
  const ageingQ = useQuery({ queryKey: ['ageing'], queryFn: () => getAgeing() })
  const payerQ = useQuery({ queryKey: ['payer-performance'], queryFn: () => getPayerPerformance() })
  const monthlyQ = useQuery({ queryKey: ['monthly'], queryFn: () => getMonthly() })
  const statusQ = useQuery({ queryKey: ['status-breakdown'], queryFn: () => getStatusBreakdown() })

  if (kpisQ.isLoading) return <Spinner />

  const kpis = kpisQ.data

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
        <KpiCard
          label="Total Claims"
          value={formatNumber(kpis?.total_claims)}
          accent="border-indigo-500"
          icon={<FileText size={20} />}
        />
        <KpiCard
          label="Total Billed"
          value={formatCurrency(kpis?.total_billed)}
          accent="border-blue-500"
          icon={<DollarSign size={20} />}
        />
        <KpiCard
          label="Approved"
          value={formatCurrency(kpis?.total_approved)}
          accent="border-emerald-500"
          icon={<CheckCircle size={20} />}
        />
        <KpiCard
          label="Paid"
          value={formatCurrency(kpis?.total_paid)}
          accent="border-green-500"
          icon={<TrendingUp size={20} />}
        />
        <KpiCard
          label="Outstanding"
          value={formatCurrency(kpis?.total_outstanding)}
          accent="border-amber-500"
          icon={<AlertCircle size={20} />}
        />
        <KpiCard
          label="Approval Rate"
          value={`${kpis?.approval_rate?.toFixed(1) ?? 0}%`}
          sub={`TDS: ${formatCurrency(kpis?.total_tds)}`}
          accent="border-purple-500"
          icon={<Clock size={20} />}
        />
      </div>

      {/* Monthly Trend + Status Breakdown */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Monthly Trend */}
        <div className="card xl:col-span-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Monthly Trend</h2>
          {monthlyQ.isLoading ? <Spinner /> : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={monthlyQ.data?.map(m => ({
                month: m.month,
                Billed: fmt(m.total_billed),
                Approved: fmt(m.total_approved),
                Paid: fmt(m.total_paid),
              }))}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`} />
                <Tooltip formatter={(v: number) => formatCurrency(v)} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="Billed" fill="#6366f1" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Approved" fill="#10b981" radius={[3, 3, 0, 0]} />
                <Bar dataKey="Paid" fill="#f59e0b" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Status Breakdown */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Claim Status</h2>
          {statusQ.isLoading ? <Spinner /> : (
            <>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={statusQ.data}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={70}
                    innerRadius={40}
                    paddingAngle={3}
                  >
                    {statusQ.data?.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => [`${v} claims`, '']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1.5 mt-2">
                {statusQ.data?.map((s, i) => (
                  <div key={s.status} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: COLORS[i % COLORS.length] }} />
                      <span className="text-gray-600 text-xs">{s.status}</span>
                    </div>
                    <span className="font-medium text-gray-800 text-xs">{s.count}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* TAT Cards + Ageing */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* TAT Summary */}
        <div className="card">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Avg. Turnaround Time</h2>
          {tatQ.isLoading ? <Spinner /> : (
            <div className="space-y-3">
              {[
                { label: 'Pre-authorisation', val: tatQ.data?.preauth_avg_days },
                { label: 'Discharge', val: tatQ.data?.discharge_avg_days },
                { label: 'Submission', val: tatQ.data?.submission_avg_days },
                { label: 'Payment', val: tatQ.data?.payment_avg_days },
                { label: 'Query Resolution', val: tatQ.data?.query_resolution_avg_days },
              ].map(({ label, val }) => (
                <div key={label} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                  <span className="text-sm text-gray-600">{label}</span>
                  <span className="font-semibold text-gray-900 text-sm tabular-nums">{formatDays(val)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Ageing Buckets */}
        <div className="card xl:col-span-2">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Outstanding Ageing</h2>
          {ageingQ.isLoading ? <Spinner /> : ageingQ.data && ageingQ.data.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={ageingQ.data.map(a => ({
                bucket: a.bucket,
                Claims: a.claim_count,
                Outstanding: fmt(a.outstanding_amt),
              }))} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v: number) => formatNumber(v)} />
                <YAxis type="category" dataKey="bucket" width={55} tick={{ fontSize: 11 }} />
                <Tooltip formatter={(v: number, name: string) => [name === 'Outstanding' ? formatCurrency(v) : v, name]} />
                <Bar dataKey="Claims" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              No outstanding amounts
            </div>
          )}
        </div>
      </div>

      {/* Payer Performance */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Payer-wise Performance</h2>
        {payerQ.isLoading ? <Spinner /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  {['Payer Type', 'Claims', 'Billed', 'Approved', 'Paid', 'Approval %'].map(h => (
                    <th key={h} className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {payerQ.data?.map(p => (
                  <tr key={p.payer_type} className="hover:bg-gray-50">
                    <td className="py-2.5 px-3 font-medium text-gray-800">{p.payer_type}</td>
                    <td className="py-2.5 px-3 text-gray-600">{p.claim_count}</td>
                    <td className="py-2.5 px-3 text-gray-600 tabular-nums">{formatCurrency(p.total_billed)}</td>
                    <td className="py-2.5 px-3 text-gray-600 tabular-nums">{formatCurrency(p.total_approved)}</td>
                    <td className="py-2.5 px-3 text-gray-600 tabular-nums">{formatCurrency(p.total_paid)}</td>
                    <td className="py-2.5 px-3">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${p.approval_rate}%` }} />
                        </div>
                        <span className="text-xs font-medium text-gray-700 tabular-nums w-10">{p.approval_rate.toFixed(1)}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
