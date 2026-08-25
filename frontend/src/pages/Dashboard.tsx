import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import KpiCard from '../components/ui/KpiCard'
import Spinner from '../components/ui/Spinner'
import WorkflowStage from '../components/ui/WorkflowStage'
import ClaimsDrilldownModal, { DrilldownViewMode } from '../components/ui/ClaimsDrilldownModal'
import {
  getKPIs,
  getTATDetailed,
  getAgeingByPayer,
  getTopDisallowances,
  getStatusSnapshot,
  getPayerPerformance,
  getMonthly,
  getMonthlyDetailed,
  getStatusBreakdown,
} from '../api/analytics'
import { ClaimFilters } from '../api/claims'
import { formatCurrency, formatNumber } from '../lib/format'
import {
  TrendingUp,
  Clock,
  CheckCircle,
  DollarSign,
  FileText,
  Percent,
  ArrowRight,
  ShieldAlert,
  Wallet,
} from 'lucide-react'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899', '#14b8a6']

const fmt = (v: string | number | undefined) => {
  if (!v) return 0
  return typeof v === 'string' ? parseFloat(v) : v
}

interface DrilldownState {
  isOpen: boolean
  title: string
  subtitle?: string
  badgeText?: string
  badgeColor?: string
  viewMode?: DrilldownViewMode
  tatStage?: string
  filters: ClaimFilters
}

export default function Dashboard() {
  const kpisQ = useQuery({ queryKey: ['kpis'], queryFn: () => getKPIs() })
  const tatDetailedQ = useQuery({ queryKey: ['tat-detailed'], queryFn: () => getTATDetailed() })
  const ageingByPayerQ = useQuery({ queryKey: ['ageing-by-payer'], queryFn: () => getAgeingByPayer() })
  const disallowancesQ = useQuery({ queryKey: ['top-disallowances'], queryFn: () => getTopDisallowances() })
  const statusSnapshotQ = useQuery({ queryKey: ['status-snapshot'], queryFn: () => getStatusSnapshot() })
  const payerQ = useQuery({ queryKey: ['payer-performance'], queryFn: () => getPayerPerformance() })
  const monthlyQ = useQuery({ queryKey: ['monthly'], queryFn: () => getMonthly() })
  const monthlyDetailedQ = useQuery({ queryKey: ['monthly-detailed'], queryFn: () => getMonthlyDetailed() })
  const statusQ = useQuery({ queryKey: ['status-breakdown'], queryFn: () => getStatusBreakdown() })

  const [drilldown, setDrilldown] = useState<DrilldownState>({
    isOpen: false,
    title: '',
    filters: {},
  })

  const openDrilldown = (config: Omit<DrilldownState, 'isOpen'>) => {
    setDrilldown({ ...config, isOpen: true })
  }

  const closeDrilldown = () => {
    setDrilldown((prev) => ({ ...prev, isOpen: false }))
  }

  if (kpisQ.isLoading) return <Spinner />

  const kpis = kpisQ.data
  const latestMonth = monthlyQ.data && monthlyQ.data.length > 0 ? monthlyQ.data[monthlyQ.data.length - 1].month : undefined

  // Custom Interactive Tooltip for Monthly Trend Chart
  const CustomMonthlyTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 rounded-xl shadow-xl border border-gray-100 text-xs space-y-2 select-none pointer-events-auto">
          <div className="flex items-center justify-between border-b border-gray-100 pb-1.5 gap-4">
            <span className="font-bold text-gray-900">{label}</span>
            <span className="text-[10px] text-gray-400 font-medium">{data.claim_count ?? 0} claims</span>
          </div>
          <div className="space-y-1">
            <div
              onClick={() =>
                openDrilldown({
                  title: `Billed Claims · ${label}`,
                  subtitle: `Billing breakdown for ${label} (Total Billed: ${formatCurrency(data.Billed)})`,
                  badgeText: `${label} Billed`,
                  badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
                  viewMode: 'billed',
                  filters: { month_label: label, has_billed: true },
                })
              }
              className="flex items-center justify-between gap-4 p-1.5 rounded-lg hover:bg-blue-50 cursor-pointer text-blue-700 font-medium transition-colors group"
            >
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#6366f1]" /> Billed:
              </span>
              <span className="tabular-nums font-bold text-blue-900 group-hover:underline">
                {formatCurrency(data.Billed)} →
              </span>
            </div>

            <div
              onClick={() =>
                openDrilldown({
                  title: `Approved Claims · ${label}`,
                  subtitle: `Approval breakdown for ${label} (Total Approved: ${formatCurrency(data.Approved)})`,
                  badgeText: `${label} Approved`,
                  badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                  viewMode: 'approved',
                  filters: { month_label: label, has_approved: true },
                })
              }
              className="flex items-center justify-between gap-4 p-1.5 rounded-lg hover:bg-emerald-50 cursor-pointer text-emerald-700 font-medium transition-colors group"
            >
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" /> Approved:
              </span>
              <span className="tabular-nums font-bold text-emerald-900 group-hover:underline">
                {formatCurrency(data.Approved)} →
              </span>
            </div>

            <div
              onClick={() =>
                openDrilldown({
                  title: `Paid Claims · ${label}`,
                  subtitle: `Payment settlement breakdown for ${label} (Total Paid: ${formatCurrency(data.Paid)})`,
                  badgeText: `${label} Paid`,
                  badgeColor: 'bg-green-100 text-green-800 border-green-200',
                  viewMode: 'paid',
                  filters: { month_label: label, has_paid: true },
                })
              }
              className="flex items-center justify-between gap-4 p-1.5 rounded-lg hover:bg-amber-50 cursor-pointer text-amber-700 font-medium transition-colors group"
            >
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]" /> Paid:
              </span>
              <span className="tabular-nums font-bold text-amber-900 group-hover:underline">
                {formatCurrency(data.Paid)} →
              </span>
            </div>
          </div>
          <p className="text-[10px] text-gray-400 text-center pt-1 border-t border-gray-50">
            Click any row to open that metric's table
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="space-y-6">
      {/* ── 1. EXECUTIVE SUMMARY (KPIs) ───────────────────────────────────────── */}
      <div className="space-y-2">
        <div className="flex items-center justify-between px-0.5">
          <h2 className="text-sm font-bold text-gray-800 uppercase tracking-wider">
            Executive Summary
          </h2>
          <span className="text-xs text-indigo-600 font-medium">Click any card to inspect records</span>
        </div>

        {/* Spacious 4x2 Grid for Perfect Readability with Zero Clipping */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KpiCard
            label="Total Claims"
            value={formatNumber(kpis?.total_claims)}
            sub="Registered cashless cases"
            badge="All Claims"
            badgeColor="bg-indigo-50 text-indigo-700"
            icon={<FileText size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Total Claims',
                subtitle: 'All registered cashless claims across all departments',
                badgeText: `${formatNumber(kpis?.total_claims)} Claims`,
                viewMode: 'overview',
                filters: {},
              })
            }
          />
          <KpiCard
            label="Total Billed"
            value={formatCurrency(kpis?.total_billed)}
            sub="Gross claim submission"
            badge="Billed"
            badgeColor="bg-blue-50 text-blue-700"
            icon={<DollarSign size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Billed Claims Breakdown',
                subtitle: `Total Billed Volume: ${formatCurrency(kpis?.total_billed)} across claims`,
                badgeText: formatCurrency(kpis?.total_billed),
                badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
                viewMode: 'billed',
                filters: { has_billed: true },
              })
            }
          />
          <KpiCard
            label="Total Approved"
            value={formatCurrency(kpis?.total_approved)}
            sub={`${kpis?.approval_rate?.toFixed(1) ?? 0}% overall approval rate`}
            badge="Approved"
            badgeColor="bg-emerald-50 text-emerald-700"
            icon={<CheckCircle size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Approved Claims & Disallowances',
                subtitle: `Total Insurer Approved Amount: ${formatCurrency(kpis?.total_approved)}`,
                badgeText: formatCurrency(kpis?.total_approved),
                badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                viewMode: 'approved',
                filters: { has_approved: true },
              })
            }
          />
          <KpiCard
            label="Total Settled"
            value={formatCurrency(kpis?.total_settled)}
            sub="Insurer settled value"
            badge="Settled"
            badgeColor="bg-teal-50 text-teal-700"
            icon={<CheckCircle size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Settled Claims Overview',
                subtitle: `Total Settled Balance: ${formatCurrency(kpis?.total_settled)} across claims`,
                badgeText: formatCurrency(kpis?.total_settled),
                badgeColor: 'bg-teal-100 text-teal-800 border-teal-200',
                viewMode: 'paid',
                filters: { has_paid: true },
              })
            }
          />

          <KpiCard
            label="Total Paid"
            value={formatCurrency(kpis?.total_paid)}
            sub={`${kpis?.collection_rate?.toFixed(1) ?? 0}% collection efficiency`}
            badge="Paid"
            badgeColor="bg-green-50 text-green-700"
            icon={<TrendingUp size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Paid Claims & Settlements',
                subtitle: `Total Payments Received: ${formatCurrency(kpis?.total_paid)} with UTR details`,
                badgeText: formatCurrency(kpis?.total_paid),
                badgeColor: 'bg-green-100 text-green-800 border-green-200',
                viewMode: 'paid',
                filters: { has_paid: true },
              })
            }
          />
          <KpiCard
            label="Total Outstanding"
            value={formatCurrency(kpis?.total_outstanding)}
            sub="Pending receivable balance"
            badge="Unsettled"
            badgeColor="bg-amber-50 text-amber-700"
            icon={<Wallet size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Outstanding & Unsettled Claims',
                subtitle: `Total Pending Outstanding Balance: ${formatCurrency(kpis?.total_outstanding)}`,
                badgeText: formatCurrency(kpis?.total_outstanding),
                badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
                viewMode: 'outstanding',
                filters: { has_outstanding: true },
              })
            }
          />
          <KpiCard
            label="Total Deductions"
            value={formatCurrency(kpis?.total_deductions)}
            sub="Disallowances & non-medicals"
            badge="Deductions"
            badgeColor="bg-rose-50 text-rose-700"
            icon={<ShieldAlert size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Disallowances & Deductions',
                subtitle: `Total Claims Deductions: ${formatCurrency(kpis?.total_deductions)}`,
                badgeText: formatCurrency(kpis?.total_deductions),
                badgeColor: 'bg-rose-100 text-rose-800 border-rose-200',
                viewMode: 'disallowance',
                filters: { has_disallowed: true },
              })
            }
          />
          <KpiCard
            label="Approval Rate"
            value={`${kpis?.approval_rate?.toFixed(1) ?? 0}%`}
            sub={`TDS: ${formatCurrency(kpis?.total_tds)}`}
            badge="Performance"
            badgeColor="bg-purple-50 text-purple-700"
            icon={<Percent size={18} />}
            onClick={() =>
              openDrilldown({
                title: 'Approval Performance & Deductions',
                subtitle: `Overall Approval Rate: ${kpis?.approval_rate?.toFixed(1) ?? 0}% · Total TDS: ${formatCurrency(kpis?.total_tds)}`,
                badgeText: `${kpis?.approval_rate?.toFixed(1) ?? 0}% Rate`,
                badgeColor: 'bg-purple-100 text-purple-800 border-purple-200',
                viewMode: 'approval_rate',
                filters: { has_approved: true },
              })
            }
          />
        </div>
      </div>

      {/* ── 2. VISUAL CHARTS (Brought to the top directly below KPIs) ────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Monthly Trend BarChart */}
        <div className="card xl:col-span-2 flex flex-col">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">
                Monthly Trend
              </h2>
              <p className="text-xs text-gray-400">Click any individual bar or metric button to inspect</p>
            </div>

            {/* Quick Action Pill Buttons for Individual Metrics */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                onClick={() =>
                  openDrilldown({
                    title: `Billed Claims ${latestMonth ? `· ${latestMonth}` : ''}`,
                    subtitle: `Billed claims overview and procedure amounts`,
                    badgeText: 'Billed',
                    badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
                    viewMode: 'billed',
                    filters: { month_label: latestMonth, has_billed: true },
                  })
                }
                className="px-2 py-1 rounded-md text-xs font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors flex items-center gap-1"
              >
                <span className="w-2 h-2 rounded-full bg-[#6366f1]" /> Billed
              </button>

              <button
                onClick={() =>
                  openDrilldown({
                    title: `Approved Claims ${latestMonth ? `· ${latestMonth}` : ''}`,
                    subtitle: `Insurer approvals and disallowance details`,
                    badgeText: 'Approved',
                    badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                    viewMode: 'approved',
                    filters: { month_label: latestMonth, has_approved: true },
                  })
                }
                className="px-2 py-1 rounded-md text-xs font-semibold bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition-colors flex items-center gap-1"
              >
                <span className="w-2 h-2 rounded-full bg-[#10b981]" /> Approved
              </button>

              <button
                onClick={() =>
                  openDrilldown({
                    title: `Paid Claims ${latestMonth ? `· ${latestMonth}` : ''}`,
                    subtitle: `Settlement payments, TDS, and UTR receipts`,
                    badgeText: 'Paid',
                    badgeColor: 'bg-green-100 text-green-800 border-green-200',
                    viewMode: 'paid',
                    filters: { month_label: latestMonth, has_paid: true },
                  })
                }
                className="px-2 py-1 rounded-md text-xs font-semibold bg-amber-50 text-amber-700 hover:bg-amber-100 transition-colors flex items-center gap-1"
              >
                <span className="w-2 h-2 rounded-full bg-[#f59e0b]" /> Paid
              </button>
            </div>
          </div>

          {monthlyQ.isLoading ? (
            <Spinner />
          ) : (
            <div className="flex-1">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={monthlyQ.data?.map((m) => ({
                    month: m.month,
                    Billed: fmt(m.total_billed),
                    Approved: fmt(m.total_approved),
                    Paid: fmt(m.total_paid),
                    claim_count: m.claim_count,
                  }))}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={(v: number) => `₹${(v / 100000).toFixed(0)}L`} />
                  <Tooltip content={<CustomMonthlyTooltip />} />

                  {/* Individual Billed Bar */}
                  <Bar dataKey="Billed" fill="#6366f1" radius={[3, 3, 0, 0]}>
                    {monthlyQ.data?.map((entry, index) => (
                      <Cell
                        key={`cell-billed-${index}`}
                        cursor="pointer"
                        className="hover:opacity-80 transition-opacity"
                        onClick={(e: any) => {
                          e?.stopPropagation?.()
                          openDrilldown({
                            title: `Billed Claims · ${entry.month}`,
                            subtitle: `Claims billed in ${entry.month} (Total Billed: ${formatCurrency(entry.total_billed)})`,
                            badgeText: `${entry.month} · Billed`,
                            badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
                            viewMode: 'billed',
                            filters: { month_label: entry.month, has_billed: true },
                          })
                        }}
                      />
                    ))}
                  </Bar>

                  {/* Individual Approved Bar */}
                  <Bar dataKey="Approved" fill="#10b981" radius={[3, 3, 0, 0]}>
                    {monthlyQ.data?.map((entry, index) => (
                      <Cell
                        key={`cell-apprv-${index}`}
                        cursor="pointer"
                        className="hover:opacity-80 transition-opacity"
                        onClick={(e: any) => {
                          e?.stopPropagation?.()
                          openDrilldown({
                            title: `Approved Claims · ${entry.month}`,
                            subtitle: `Claims approved in ${entry.month} (Total Approved: ${formatCurrency(entry.total_approved)})`,
                            badgeText: `${entry.month} · Approved`,
                            badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                            viewMode: 'approved',
                            filters: { month_label: entry.month, has_approved: true },
                          })
                        }}
                      />
                    ))}
                  </Bar>

                  {/* Individual Paid Bar */}
                  <Bar dataKey="Paid" fill="#f59e0b" radius={[3, 3, 0, 0]}>
                    {monthlyQ.data?.map((entry, index) => (
                      <Cell
                        key={`cell-paid-${index}`}
                        cursor="pointer"
                        className="hover:opacity-80 transition-opacity"
                        onClick={(e: any) => {
                          e?.stopPropagation?.()
                          openDrilldown({
                            title: `Paid Claims · ${entry.month}`,
                            subtitle: `Claims paid in ${entry.month} (Total Paid: ${formatCurrency(entry.total_paid)})`,
                            badgeText: `${entry.month} · Paid`,
                            badgeColor: 'bg-green-100 text-green-800 border-green-200',
                            viewMode: 'paid',
                            filters: { month_label: entry.month, has_paid: true },
                          })
                        }}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              {/* Clickable Legend Below Chart */}
              <div className="flex items-center justify-center gap-6 mt-2 text-xs">
                <button
                  onClick={() =>
                    openDrilldown({
                      title: 'All Billed Claims',
                      subtitle: 'Billed claims across all months',
                      badgeText: 'Billed Focus',
                      badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
                      viewMode: 'billed',
                      filters: { has_billed: true },
                    })
                  }
                  className="flex items-center gap-1.5 text-gray-600 hover:text-indigo-600 font-medium transition-colors"
                >
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#6366f1]" />
                  <span>Billed (Click to view)</span>
                </button>

                <button
                  onClick={() =>
                    openDrilldown({
                      title: 'All Approved Claims',
                      subtitle: 'Approved claims with approval rate statistics',
                      badgeText: 'Approved Focus',
                      badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                      viewMode: 'approved',
                      filters: { has_approved: true },
                    })
                  }
                  className="flex items-center gap-1.5 text-gray-600 hover:text-emerald-600 font-medium transition-colors"
                >
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#10b981]" />
                  <span>Approved (Click to view)</span>
                </button>

                <button
                  onClick={() =>
                    openDrilldown({
                      title: 'All Paid Claims',
                      subtitle: 'Settled claims with payment receipts & UTR numbers',
                      badgeText: 'Paid Focus',
                      badgeColor: 'bg-green-100 text-green-800 border-green-200',
                      viewMode: 'paid',
                      filters: { has_paid: true },
                    })
                  }
                  className="flex items-center gap-1.5 text-gray-600 hover:text-amber-600 font-medium transition-colors"
                >
                  <span className="w-2.5 h-2.5 rounded-xs bg-[#f59e0b]" />
                  <span>Paid (Click to view)</span>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Status Breakdown Donut Chart */}
        <div className="card flex flex-col">
          <div className="flex items-center justify-between mb-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">
                Claim Status Breakdown
              </h2>
              <p className="text-xs text-gray-400">Click a slice or status to view</p>
            </div>
            <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
              Interactive
            </span>
          </div>

          {statusQ.isLoading ? (
            <Spinner />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={175}>
                <PieChart>
                  <Pie
                    data={statusQ.data}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={68}
                    innerRadius={40}
                    paddingAngle={3}
                    cursor="pointer"
                    onClick={(entry: any) => {
                      if (entry && entry.status) {
                        openDrilldown({
                          title: `Claims · ${entry.status}`,
                          subtitle: `Claims with status: ${entry.status} (${entry.count} records)`,
                          badgeText: `${entry.count} Claims`,
                          viewMode: 'status',
                          filters: { status: entry.status },
                        })
                      }
                    }}
                  >
                    {statusQ.data?.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} className="hover:opacity-80 transition-opacity" />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => [`${v} claims`, '']} />
                </PieChart>
              </ResponsiveContainer>

              <div className="space-y-1 mt-2 flex-1 overflow-y-auto max-h-[160px] pr-1">
                {statusQ.data?.map((s, i) => (
                  <div
                    key={s.status}
                    onClick={() =>
                      openDrilldown({
                        title: `Claims · ${s.status}`,
                        subtitle: `Claims with final status: ${s.status}`,
                        badgeText: `${s.count} Claims`,
                        viewMode: 'status',
                        filters: { status: s.status },
                      })
                    }
                    className="flex items-center justify-between text-sm py-1.5 px-2 rounded-lg cursor-pointer hover:bg-indigo-50/80 transition-all group"
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ background: COLORS[i % COLORS.length] }}
                      />
                      <span className="text-gray-600 text-xs group-hover:text-indigo-600 group-hover:font-medium transition-colors">
                        {s.status}
                      </span>
                    </div>
                    <span className="font-semibold text-gray-800 text-xs bg-gray-50 group-hover:bg-indigo-100 group-hover:text-indigo-700 px-2 py-0.5 rounded-full transition-colors">
                      {s.count}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── 3. OPERATIONAL TAT & TOP DISALLOWANCES ────────────────────────────── */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Operational TAT */}
        <div className="card">
          <div className="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">
                Operational Turnaround Time (TAT)
              </h2>
              <p className="text-xs text-gray-400">Benchmark SLA turnaround durations across claim milestones</p>
            </div>
            <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
              Click row to view
            </span>
          </div>

          {tatDetailedQ.isLoading ? (
            <Spinner />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-50 text-gray-600 border-b border-gray-100">
                    <th className="text-left py-2 px-3 font-semibold">Metric</th>
                    <th className="text-right py-2 px-3 font-semibold">Average</th>
                    <th className="text-right py-2 px-3 font-semibold">Fastest</th>
                    <th className="text-right py-2 px-3 font-semibold">Slowest</th>
                    <th className="text-right py-2 px-3 font-semibold">Target</th>
                    <th className="text-center py-2 px-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {tatDetailedQ.data?.map((r) => (
                    <tr
                      key={r.metric}
                      onClick={() =>
                        openDrilldown({
                          title: `${r.metric} Claims`,
                          subtitle: `Claims with recorded ${r.metric.toLowerCase()} duration (Avg: ${r.average} days)`,
                          badgeText: `Avg: ${r.average}d`,
                          badgeColor:
                            r.status === 'Above Target'
                              ? 'bg-rose-100 text-rose-800 border-rose-200'
                              : 'bg-emerald-100 text-emerald-800 border-emerald-200',
                          viewMode: 'tat',
                          tatStage: r.stage,
                          filters: { tat_stage: r.stage },
                        })
                      }
                      className="hover:bg-indigo-50/70 cursor-pointer transition-colors group"
                    >
                      <td className="py-2.5 px-3 font-medium text-gray-800 group-hover:text-indigo-600 flex items-center gap-1.5">
                        <Clock size={13} className="text-gray-400 group-hover:text-indigo-600" />
                        {r.metric}
                      </td>
                      <td className="py-2.5 px-3 text-right font-semibold text-gray-900 tabular-nums">
                        {r.average.toFixed(1)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-gray-500 tabular-nums">
                        {r.fastest.toFixed(1)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-gray-500 tabular-nums">
                        {r.slowest.toFixed(1)}
                      </td>
                      <td className="py-2.5 px-3 text-right text-gray-500 tabular-nums font-medium">
                        {r.target.toFixed(1)}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                            r.status === 'Above Target'
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}
                        >
                          {r.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Top Disallowances */}
        <div className="card flex flex-col">
          <div className="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
            <div>
              <h2 className="text-sm font-semibold text-gray-800">
                Top Disallowances
              </h2>
              <p className="text-xs text-gray-400">Claims deductions categorized by hospital denial reasons</p>
            </div>
            <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
              Click reason to view
            </span>
          </div>

          {disallowancesQ.isLoading ? (
            <Spinner />
          ) : !disallowancesQ.data || disallowancesQ.data.length === 0 ? (
            <div className="py-12 text-center text-xs text-gray-400">
              No disallowances recorded
            </div>
          ) : (
            <div className="overflow-x-auto flex-1 max-h-[260px] overflow-y-auto pr-1">
              <table className="w-full text-xs">
                <thead className="sticky top-0 bg-slate-50 border-b border-gray-100">
                  <tr className="text-gray-600">
                    <th className="text-left py-2 px-3 font-semibold">Reason</th>
                    <th className="text-right py-2 px-3 font-semibold">Cases</th>
                    <th className="text-right py-2 px-3 font-semibold">Disallowed (₹)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {disallowancesQ.data?.map((d) => (
                    <tr
                      key={d.reason}
                      onClick={() =>
                        openDrilldown({
                          title: `Disallowances · ${d.reason}`,
                          subtitle: `Claims with deductions under reason: ${d.reason} (${d.cases_count} cases)`,
                          badgeText: `${d.cases_count} Cases · ${formatCurrency(d.disallowed_amt)}`,
                          badgeColor: 'bg-rose-100 text-rose-800 border-rose-200',
                          viewMode: 'disallowance',
                          filters: { disallowed_reason: d.reason, has_disallowed: true },
                        })
                      }
                      className="hover:bg-indigo-50/70 cursor-pointer transition-colors group"
                    >
                      <td className="py-1.5 px-3 font-medium text-gray-700 group-hover:text-indigo-600">
                        {d.reason}
                      </td>
                      <td className="py-1.5 px-3 text-right text-gray-600 tabular-nums">
                        {d.cases_count}
                      </td>
                      <td className="py-1.5 px-3 text-right font-semibold text-gray-900 tabular-nums">
                        {formatCurrency(d.disallowed_amt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* ── 4. OUTSTANDING AGEING BY PAYER ─────────────────────────────────────── */}
      <div className="card">
        <div className="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">
              Outstanding Ageing by Payer
            </h2>
            <p className="text-xs text-gray-400">Unsettled claim balances distributed across ageing duration buckets</p>
          </div>
          <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
            Click row or bucket to view
          </span>
        </div>

        {ageingByPayerQ.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 text-gray-600 border-b border-gray-100">
                  <th className="text-left py-2 px-3 font-semibold">Payer Type</th>
                  <th className="text-right py-2 px-3 font-semibold">0-30 Days</th>
                  <th className="text-right py-2 px-3 font-semibold">31-60 Days</th>
                  <th className="text-right py-2 px-3 font-semibold">61-90 Days</th>
                  <th className="text-right py-2 px-3 font-semibold">90+ Days</th>
                  <th className="text-right py-2 px-3 font-bold text-gray-900 bg-slate-100">Total Outstanding</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {ageingByPayerQ.data?.map((row) => {
                  const isGrand = row.payer_type === 'GRAND TOTAL'
                  return (
                    <tr
                      key={row.payer_type}
                      onClick={() =>
                        openDrilldown({
                          title: `Ageing Claims · ${row.payer_type}`,
                          subtitle: `Unsettled claims for ${row.payer_type} (Total Outstanding: ${formatCurrency(row.total_outstanding)})`,
                          badgeText: formatCurrency(row.total_outstanding),
                          badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
                          viewMode: 'ageing',
                          filters: {
                            payer_type: isGrand ? undefined : row.payer_type,
                            has_outstanding: true,
                          },
                        })
                      }
                      className={`${
                        isGrand ? 'bg-slate-100/90 font-bold border-t-2 border-gray-300' : 'hover:bg-indigo-50/70'
                      } cursor-pointer transition-colors group`}
                    >
                      <td className={`py-2 px-3 ${isGrand ? 'font-black text-gray-900' : 'font-medium text-gray-800 group-hover:text-indigo-600'}`}>
                        {row.payer_type}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-600">
                        {formatCurrency(row.bucket_0_30)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-600">
                        {formatCurrency(row.bucket_31_60)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-600">
                        {formatCurrency(row.bucket_61_90)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-600">
                        {formatCurrency(row.bucket_90_plus)}
                      </td>
                      <td className={`py-2 px-3 text-right tabular-nums font-bold ${isGrand ? 'text-indigo-900 bg-slate-200/80' : 'text-gray-900 bg-slate-50'}`}>
                        {formatCurrency(row.total_outstanding)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── 5. CLAIM STATUS WORKFLOW FUNNEL ───────────────────────────────────── */}
      <div className="card">
        <div className="flex items-center justify-between mb-4 border-b border-gray-100 pb-2">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">
              Claim Status Lifecycle
            </h2>
            <p className="text-xs text-gray-400">Progression workflow from Pre-Auth → Discharge → Submission</p>
          </div>
          <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
            Click status to inspect claims
          </span>
        </div>

        {statusSnapshotQ.isLoading ? (
          <Spinner />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-11 gap-4 items-center">
            {/* Stage 1: Preauth Status */}
            <WorkflowStage
              title="Preauth Status"
              titleColor="text-indigo-900"
              dotColor="bg-indigo-500"
              activeBadgeBg="bg-indigo-600"
              items={statusSnapshotQ.data?.preauth_statuses}
              onItemClick={(item) =>
                openDrilldown({
                  title: `Preauth Claims · ${item.status}`,
                  subtitle: `Claims with Preauth Status: ${item.status} (${item.count} claims)`,
                  badgeText: `${item.count} Claims`,
                  badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
                  viewMode: 'overview',
                  filters: { preauth_status: item.status },
                })
              }
            />

            {/* Connector 1 */}
            <div className="hidden md:flex md:col-span-1 justify-center text-gray-300">
              <ArrowRight size={24} className="animate-pulse text-indigo-400" />
            </div>

            {/* Stage 2: Discharge Status */}
            <WorkflowStage
              title="Discharge Status"
              titleColor="text-emerald-900"
              dotColor="bg-emerald-500"
              activeBadgeBg="bg-emerald-600"
              items={statusSnapshotQ.data?.discharge_statuses}
              onItemClick={(item) =>
                openDrilldown({
                  title: `Discharge Claims · ${item.status}`,
                  subtitle: `Claims with Discharge Status: ${item.status} (${item.count} claims)`,
                  badgeText: `${item.count} Claims`,
                  badgeColor: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                  viewMode: 'overview',
                  filters: { discharge_status: item.status },
                })
              }
            />

            {/* Connector 2 */}
            <div className="hidden md:flex md:col-span-1 justify-center text-gray-300">
              <ArrowRight size={24} className="animate-pulse text-emerald-400" />
            </div>

            {/* Stage 3: Submission Status */}
            <WorkflowStage
              title="Submission Status"
              titleColor="text-blue-900"
              dotColor="bg-blue-500"
              activeBadgeBg="bg-blue-600"
              items={statusSnapshotQ.data?.submission_statuses}
              onItemClick={(item) =>
                openDrilldown({
                  title: `Submission Claims · ${item.status}`,
                  subtitle: `Claims with Submission Status: ${item.status} (${item.count} claims)`,
                  badgeText: `${item.count} Claims`,
                  badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
                  viewMode: 'overview',
                  filters: { submission_status: item.status },
                })
              }
            />
          </div>
        )}
      </div>

      {/* ── 6. PAYER PERFORMANCE ──────────────────────────────────────────────── */}
      <div className="card">
        <div className="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">
              Payer Performance
            </h2>
            <p className="text-xs text-gray-400">Financial volumes, approval ratios, and collection rates across payer categories</p>
          </div>
          <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
            Click row to view
          </span>
        </div>

        {payerQ.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 text-gray-600 border-b border-gray-100">
                  <th className="text-left py-2 px-3 font-semibold">Payer Type</th>
                  <th className="text-right py-2 px-3 font-semibold">Claims</th>
                  <th className="text-right py-2 px-3 font-semibold">Billed (₹)</th>
                  <th className="text-right py-2 px-3 font-semibold">Approved (₹)</th>
                  <th className="text-right py-2 px-3 font-semibold">Settled (₹)</th>
                  <th className="text-right py-2 px-3 font-semibold">Paid (₹)</th>
                  <th className="text-right py-2 px-3 font-semibold">Outstanding (₹)</th>
                  <th className="text-right py-2 px-3 font-semibold">Approval %</th>
                  <th className="text-right py-2 px-3 font-semibold">Deduction %</th>
                  <th className="text-right py-2 px-3 font-semibold">Collection %</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {payerQ.data?.map((p) => {
                  const isGrand = p.payer_type === 'GRAND TOTAL'
                  return (
                    <tr
                      key={p.payer_type}
                      onClick={() =>
                        openDrilldown({
                          title: `Claims Breakdown · ${p.payer_type}`,
                          subtitle: `All claims billed under payer type ${p.payer_type} (${p.claim_count} claims)`,
                          badgeText: `${p.claim_count} Claims · ${p.approval_rate.toFixed(1)}% Appr`,
                          badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
                          viewMode: 'payer',
                          filters: { payer_type: isGrand ? undefined : p.payer_type },
                        })
                      }
                      className={`${
                        isGrand ? 'bg-slate-100/90 font-bold border-t-2 border-gray-300' : 'hover:bg-indigo-50/70'
                      } cursor-pointer transition-colors group`}
                    >
                      <td className={`py-2 px-3 ${isGrand ? 'font-black text-gray-900' : 'font-medium text-gray-800 group-hover:text-indigo-600'}`}>
                        {p.payer_type}
                      </td>
                      <td className="py-2 px-3 text-right font-medium text-gray-700 tabular-nums">
                        {p.claim_count}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-700">
                        {formatCurrency(p.total_billed)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-700">
                        {formatCurrency(p.total_approved)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-gray-700">
                        {formatCurrency(p.total_settled)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums font-semibold text-emerald-700">
                        {formatCurrency(p.total_paid)}
                      </td>
                      <td className="py-2 px-3 text-right tabular-nums text-amber-700">
                        {formatCurrency(p.total_outstanding)}
                      </td>
                      <td className="py-2 px-3 text-right font-semibold text-gray-900 tabular-nums">
                        {p.approval_rate.toFixed(1)}%
                      </td>
                      <td className="py-2 px-3 text-right text-rose-600 tabular-nums">
                        {p.deduction_rate.toFixed(1)}%
                      </td>
                      <td className="py-2 px-3 text-right font-semibold text-indigo-900 tabular-nums">
                        {p.collection_rate.toFixed(1)}%
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── 7. 12-MONTH PERFORMANCE SUMMARY TABLE ─────────────────────────────── */}
      <div className="card">
        <div className="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">
              12-Month Performance Summary
            </h2>
            <p className="text-xs text-gray-400">Monthly billing, insurer approvals, TDS, and reconciliation variances</p>
          </div>
          <span className="text-[11px] font-medium text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full">
            Click month row to inspect
          </span>
        </div>

        {monthlyDetailedQ.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 text-gray-600 border-b border-gray-100">
                  <th className="text-left py-2 px-2.5 font-semibold">Month</th>
                  <th className="text-right py-2 px-2 font-semibold">Cases</th>
                  <th className="text-right py-2 px-2.5 font-semibold">Billed (₹)</th>
                  <th className="text-right py-2 px-2.5 font-semibold">Approved (₹)</th>
                  <th className="text-right py-2 px-2.5 font-semibold">Paid (₹)</th>
                  <th className="text-right py-2 px-2 font-semibold">TDS (₹)</th>
                  <th className="text-right py-2 px-2 font-semibold">Outstanding (₹)</th>
                  <th className="text-right py-2 px-2 font-semibold">Patient Paid (₹)</th>
                  <th className="text-right py-2 px-2 font-semibold">Appr %</th>
                  <th className="text-right py-2 px-2 font-semibold">Paid %</th>
                  <th className="text-right py-2 px-2 font-semibold">Net Col %</th>
                  <th className="text-right py-2 px-2 font-semibold">TDS %</th>
                  <th className="text-right py-2 px-2.5 font-semibold">Variance (₹)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {monthlyDetailedQ.data?.map((m) => (
                  <tr
                    key={m.month}
                    onClick={() =>
                      openDrilldown({
                        title: `Monthly Claims · ${m.month}`,
                        subtitle: `Claims for ${m.month} (Total Billed: ${formatCurrency(m.total_billed)}, Approved: ${formatCurrency(m.total_approved)})`,
                        badgeText: `${m.claim_count} Cases`,
                        badgeColor: 'bg-indigo-100 text-indigo-800 border-indigo-200',
                        viewMode: 'overview',
                        filters: { month_label: m.month },
                      })
                    }
                    className="hover:bg-indigo-50/70 cursor-pointer transition-colors group"
                  >
                    <td className="py-2.5 px-2.5 font-bold text-gray-900 group-hover:text-indigo-600">
                      {m.month}
                    </td>
                    <td className="py-2.5 px-2 text-right font-medium text-gray-700 tabular-nums">
                      {m.claim_count}
                    </td>
                    <td className="py-2.5 px-2.5 text-right tabular-nums text-gray-800">
                      {formatCurrency(m.total_billed)}
                    </td>
                    <td className="py-2.5 px-2.5 text-right tabular-nums text-gray-800">
                      {formatCurrency(m.total_approved)}
                    </td>
                    <td className="py-2.5 px-2.5 text-right tabular-nums font-semibold text-emerald-700">
                      {formatCurrency(m.total_paid)}
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums text-purple-700">
                      {formatCurrency(m.total_tds)}
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums text-amber-700">
                      {formatCurrency(m.total_outstanding)}
                    </td>
                    <td className="py-2.5 px-2 text-right tabular-nums text-gray-600">
                      {formatCurrency(m.patient_paid)}
                    </td>
                    <td className="py-2.5 px-2 text-right font-medium text-gray-800 tabular-nums">
                      {m.approval_rate.toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-2 text-right font-medium text-gray-800 tabular-nums">
                      {m.paid_rate.toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-2 text-right font-medium text-indigo-900 tabular-nums">
                      {m.net_collected_rate.toFixed(1)}%
                    </td>
                    <td className="py-2.5 px-2 text-right text-gray-500 tabular-nums">
                      {m.tds_rate.toFixed(1)}%
                    </td>
                    <td className={`py-2.5 px-2.5 text-right tabular-nums font-semibold ${parseFloat(m.variance) < 0 ? 'text-rose-600' : 'text-gray-900'}`}>
                      {formatCurrency(m.variance)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Drill-down Claims Modal Popup */}
      <ClaimsDrilldownModal
        isOpen={drilldown.isOpen}
        onClose={closeDrilldown}
        title={drilldown.title}
        subtitle={drilldown.subtitle}
        badgeText={drilldown.badgeText}
        badgeColor={drilldown.badgeColor}
        viewMode={drilldown.viewMode}
        tatStage={drilldown.tatStage}
        filters={drilldown.filters}
      />
    </div>
  )
}
