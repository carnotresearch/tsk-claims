import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  X,
  Search,
  ExternalLink,
  Download,
  ChevronLeft,
  ChevronRight,
  FileSpreadsheet,
  Layers,
  ArrowRight,
  DollarSign,
  CheckCircle,
  TrendingUp,
  AlertCircle,
  Clock,
  Building,
} from 'lucide-react'
import { getClaims, ClaimFilters } from '../../api/claims'
import { formatCurrency, formatDate, formatNumber, formatDays } from '../../lib/format'
import Badge from './Badge'
import Spinner from './Spinner'

export type DrilldownViewMode =
  | 'overview'
  | 'billed'
  | 'approved'
  | 'paid'
  | 'outstanding'
  | 'approval_rate'
  | 'tat'
  | 'ageing'
  | 'payer'
  | 'status'
  | 'disallowance'

interface Props {
  isOpen: boolean
  onClose: () => void
  title: string
  subtitle?: string
  badgeText?: string
  badgeColor?: string
  viewMode?: DrilldownViewMode
  tatStage?: string
  filters: ClaimFilters
}

export default function ClaimsDrilldownModal({
  isOpen,
  onClose,
  title,
  subtitle,
  badgeText,
  badgeColor = 'bg-indigo-100 text-indigo-800 border-indigo-200',
  viewMode = 'overview',
  tatStage,
  filters,
}: Props) {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState(filters.status || '')
  const [activeTab, setActiveTab] = useState<'focused' | 'financials' | 'timeline' | 'all'>('focused')

  // Reset page, search & tab whenever the modal opens or filters change
  useEffect(() => {
    if (isOpen) {
      setPage(1)
      setSearch('')
      setStatusFilter(filters.status || '')
      setActiveTab('focused')
    }
  }, [isOpen, filters, viewMode])

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const combinedFilters: ClaimFilters = {
    ...filters,
    page,
    page_size: 20,
    search: search.trim() || undefined,
    status: statusFilter || filters.status || undefined,
  }

  const { data, isLoading } = useQuery({
    queryKey: ['drilldown-claims', combinedFilters],
    queryFn: () => getClaims(combinedFilters),
    enabled: isOpen,
    placeholderData: (prev) => prev,
  })

  if (!isOpen) return null

  const totalClaims = data?.total ?? 0
  const items = data?.items ?? []

  // Dynamic calculations for the subset
  const sumBilled = items.reduce((acc, c) => acc + (c.final_claimed_amt ? parseFloat(c.final_claimed_amt) : 0), 0)
  const sumApproved = items.reduce((acc, c) => acc + (c.final_bill_approved_amt ? parseFloat(c.final_bill_approved_amt) : 0), 0)
  const sumPaid = items.reduce((acc, c) => acc + (c.payment_received_amt ? parseFloat(c.payment_received_amt) : 0), 0)
  const sumOutstanding = items.reduce((acc, c) => acc + (c.outstanding_amt ? parseFloat(c.outstanding_amt) : 0), 0)
  const sumDisallowed = items.reduce((acc, c) => acc + (c.disallowed_amt ? parseFloat(c.disallowed_amt) : 0), 0)
  const sumTds = items.reduce((acc, c) => acc + (c.tds_amt ? parseFloat(c.tds_amt) : 0), 0)
  const sumPreauthReq = items.reduce((acc, c) => acc + (c.preauth_requested_amt ? parseFloat(c.preauth_requested_amt) : 0), 0)
  const sumHospitalDiscount = items.reduce((acc, c) => acc + (c.hospital_discount ? parseFloat(c.hospital_discount) : 0), 0)
  const sumPatientPaid = items.reduce((acc, c) => acc + (c.patient_paid_amt ? parseFloat(c.patient_paid_amt) : 0), 0)

  const avgBilled = items.length ? sumBilled / items.length : 0
  const avgApproved = items.length ? sumApproved / items.length : 0
  const overallApprovalRate = sumBilled > 0 ? (sumApproved / sumBilled) * 100 : 0

  // TAT stats for stage
  const validTats = items
    .map((c) => {
      if (tatStage === 'preauth') return c.preauth_tat
      if (tatStage === 'discharge') return c.discharge_tat
      if (tatStage === 'submission') return c.submission_tat
      if (tatStage === 'payment') return c.payment_tat
      if (tatStage === 'query') return c.query_resolution_tat
      return c.preauth_tat ?? c.discharge_tat ?? c.submission_tat ?? c.payment_tat
    })
    .filter((v): v is number => v !== null && v !== undefined)

  const avgTat = validTats.length ? validTats.reduce((a, b) => a + b, 0) / validTats.length : null
  const minTat = validTats.length ? Math.min(...validTats) : null
  const maxTat = validTats.length ? Math.max(...validTats) : null

  // Navigate to full claims list with filters
  const handleOpenInClaimsPage = () => {
    const params = new URLSearchParams()
    if (filters.status) params.set('status', filters.status)
    if (filters.payer_type) params.set('payer', filters.payer_type)
    if (filters.ageing_bucket) params.set('ageing', filters.ageing_bucket)
    if (filters.month_label) params.set('month', filters.month_label)
    if (search) params.set('search', search)
    navigate(`/claims${params.toString() ? `?${params.toString()}` : ''}`)
  }

  // Export current list to CSV
  const handleExportCSV = () => {
    if (!items.length) return
    const headers = [
      'HSK Ref',
      'Patient Name',
      'Admission Date',
      'Discharge Date',
      'Procedure',
      'Payer Type',
      'Insurer Name',
      'Billed (INR)',
      'Preauth Approved (INR)',
      'Final Approved (INR)',
      'Disallowed (INR)',
      'Settled (INR)',
      'Paid (INR)',
      'TDS (INR)',
      'UTR No',
      'Payment Mode',
      'Outstanding (INR)',
      'Ageing Days',
      'Ageing Bucket',
      'Preauth TAT',
      'Payment TAT',
      'Status',
    ]

    const rows = items.map((c) => [
      `"${c.hsk_ref_id ?? ''}"`,
      `"${c.patient_name ?? ''}"`,
      `"${c.date_admission ?? ''}"`,
      `"${c.date_discharge ?? ''}"`,
      `"${c.procedure_name ?? ''}"`,
      `"${c.payer_type ?? ''}"`,
      `"${c.insurer_name ?? ''}"`,
      c.final_claimed_amt ?? '0',
      c.preauth_approved_amt ?? '0',
      c.final_bill_approved_amt ?? '0',
      c.disallowed_amt ?? '0',
      c.settled_amt ?? '0',
      c.payment_received_amt ?? '0',
      c.tds_amt ?? '0',
      `"${c.utr_no ?? ''}"`,
      `"${c.payment_mode ?? ''}"`,
      c.outstanding_amt ?? '0',
      c.ageing_days ?? '',
      `"${c.ageing_bucket ?? ''}"`,
      c.preauth_tat ?? '',
      c.payment_tat ?? '',
      `"${c.final_claim_status ?? ''}"`,
    ])

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.setAttribute('href', url)
    link.setAttribute('download', `claims_${viewMode}_${title.toLowerCase().replace(/[^a-z0-9]/g, '_')}_p${page}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Get icon for viewMode
  const getViewIcon = () => {
    switch (viewMode) {
      case 'billed':
        return <DollarSign size={20} className="text-blue-600" />
      case 'approved':
      case 'approval_rate':
        return <CheckCircle size={20} className="text-emerald-600" />
      case 'paid':
        return <TrendingUp size={20} className="text-green-600" />
      case 'outstanding':
      case 'ageing':
        return <AlertCircle size={20} className="text-amber-600" />
      case 'tat':
        return <Clock size={20} className="text-purple-600" />
      case 'payer':
        return <Building size={20} className="text-indigo-600" />
      default:
        return <Layers size={20} className="text-indigo-600" />
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 md:p-6 bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
      {/* Modal Box */}
      <div
        className="bg-white w-full max-w-7xl max-h-[94vh] rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden animate-scaleIn"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-3.5 border-b border-gray-100 flex items-center justify-between bg-white shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-slate-50 border border-gray-100 rounded-xl">{getViewIcon()}</div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="text-base font-bold text-gray-900">{title}</h2>
                {badgeText && (
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badgeColor}`}
                  >
                    {badgeText}
                  </span>
                )}
                {filters.month_label && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
                    Month: {filters.month_label}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-0.5">
                {subtitle ?? `Detailed records and metric breakdown`}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleExportCSV}
              title="Export filtered records to CSV"
              className="btn-secondary py-1.5 px-3 text-xs flex items-center gap-1.5"
              disabled={items.length === 0}
            >
              <Download size={13} />
              <span className="hidden sm:inline">Export CSV</span>
            </button>
            <button
              onClick={handleOpenInClaimsPage}
              title="Open with filters in full claims page"
              className="btn-secondary py-1.5 px-3 text-xs text-indigo-600 border-indigo-200 hover:bg-indigo-50 flex items-center gap-1.5"
            >
              <ExternalLink size={13} />
              <span className="hidden sm:inline">Full Page</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors ml-1"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Dynamic Metric-Focused Stat Cards */}
        <div className="bg-slate-50/80 border-b border-gray-100 px-6 py-3 shrink-0">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {/* Common Match Count */}
            <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
              <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                Total Matches
              </span>
              <span className="text-lg font-bold text-gray-900 mt-0.5 block">
                {formatNumber(totalClaims)}
              </span>
            </div>

            {/* Billed View Cards */}
            {viewMode === 'billed' && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-blue-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-blue-600 uppercase tracking-wider block">
                    Page Total Billed
                  </span>
                  <span className="text-lg font-bold text-blue-900 mt-0.5 block tabular-nums">
                    {formatCurrency(sumBilled)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Avg Billed / Claim
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(avgBilled)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Preauth Requested
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumPreauthReq)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Hospital Discount
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumHospitalDiscount)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Patient Paid
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumPatientPaid)}
                  </span>
                </div>
              </>
            )}

            {/* Approved / Approval Rate Cards */}
            {(viewMode === 'approved' || viewMode === 'approval_rate') && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-emerald-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-emerald-700 uppercase tracking-wider block">
                    Page Total Approved
                  </span>
                  <span className="text-lg font-bold text-emerald-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumApproved)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-purple-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-purple-700 uppercase tracking-wider block">
                    Approval Rate
                  </span>
                  <span className="text-lg font-bold text-purple-800 mt-0.5 block tabular-nums">
                    {overallApprovalRate.toFixed(1)}%
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Avg Approved / Claim
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(avgApproved)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-rose-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-rose-600 uppercase tracking-wider block">
                    Total Disallowed
                  </span>
                  <span className="text-lg font-bold text-rose-700 mt-0.5 block tabular-nums">
                    {formatCurrency(sumDisallowed)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Total Billed Ref
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumBilled)}
                  </span>
                </div>
              </>
            )}

            {/* Paid View Cards */}
            {viewMode === 'paid' && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-green-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-green-700 uppercase tracking-wider block">
                    Total Payment Received
                  </span>
                  <span className="text-lg font-bold text-green-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumPaid)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Total Approved
                  </span>
                  <span className="text-lg font-bold text-emerald-700 mt-0.5 block tabular-nums">
                    {formatCurrency(sumApproved)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Total TDS Deducted
                  </span>
                  <span className="text-lg font-bold text-purple-700 mt-0.5 block tabular-nums">
                    {formatCurrency(sumTds)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Claims with UTR
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block">
                    {items.filter((c) => !!c.utr_no).length} / {items.length}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-amber-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-amber-700 uppercase tracking-wider block">
                    Residual Balance
                  </span>
                  <span className="text-lg font-bold text-amber-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumOutstanding)}
                  </span>
                </div>
              </>
            )}

            {/* Outstanding / Ageing View Cards */}
            {(viewMode === 'outstanding' || viewMode === 'ageing') && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-amber-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-amber-700 uppercase tracking-wider block">
                    Total Outstanding
                  </span>
                  <span className="text-lg font-bold text-amber-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumOutstanding)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Total Approved Ref
                  </span>
                  <span className="text-lg font-bold text-emerald-700 mt-0.5 block tabular-nums">
                    {formatCurrency(sumApproved)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Paid So Far
                  </span>
                  <span className="text-lg font-bold text-green-700 mt-0.5 block tabular-nums">
                    {formatCurrency(sumPaid)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-red-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-red-600 uppercase tracking-wider block">
                    Ageing &gt; 60 Days
                  </span>
                  <span className="text-lg font-bold text-red-700 mt-0.5 block">
                    {
                      items.filter((c) => c.ageing_bucket === '61-90' || c.ageing_bucket === '90+')
                        .length
                    }
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Pending Claims
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block">
                    {items.filter((c) => (c.outstanding_amt ? parseFloat(c.outstanding_amt) > 0 : false)).length}
                  </span>
                </div>
              </>
            )}

            {/* TAT View Cards */}
            {viewMode === 'tat' && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-purple-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-purple-700 uppercase tracking-wider block">
                    Avg Stage TAT
                  </span>
                  <span className="text-lg font-bold text-purple-900 mt-0.5 block tabular-nums">
                    {formatDays(avgTat)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Fastest (Min TAT)
                  </span>
                  <span className="text-lg font-bold text-emerald-700 mt-0.5 block tabular-nums">
                    {formatDays(minTat)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Longest (Max TAT)
                  </span>
                  <span className="text-lg font-bold text-amber-700 mt-0.5 block tabular-nums">
                    {formatDays(maxTat)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Target SLA
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block">
                    &le; 2.0d
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Stage Processed
                  </span>
                  <span className="text-lg font-bold text-indigo-700 mt-0.5 block capitalize">
                    {tatStage ?? 'Standard'}
                  </span>
                </div>
              </>
            )}

            {/* Disallowance / Deductions View Cards */}
            {viewMode === 'disallowance' && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-rose-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-rose-700 uppercase tracking-wider block">
                    Total Disallowed
                  </span>
                  <span className="text-lg font-bold text-rose-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumDisallowed)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Page Billed Ref
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumBilled)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-emerald-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-emerald-700 uppercase tracking-wider block">
                    Page Approved
                  </span>
                  <span className="text-lg font-bold text-emerald-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumApproved)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Hospital Discount
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumHospitalDiscount)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-purple-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-purple-700 uppercase tracking-wider block">
                    Deduction Rate
                  </span>
                  <span className="text-lg font-bold text-purple-800 mt-0.5 block">
                    {sumBilled > 0 ? ((sumDisallowed / sumBilled) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              </>
            )}

            {/* Overview / Payer / Status Default Cards */}
            {(viewMode === 'overview' || viewMode === 'payer' || viewMode === 'status') && (
              <>
                <div className="bg-white p-2.5 rounded-xl border border-gray-100 shadow-2xs">
                  <span className="text-[11px] font-medium text-gray-500 uppercase tracking-wider block">
                    Page Billed
                  </span>
                  <span className="text-lg font-bold text-gray-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumBilled)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-emerald-50 shadow-2xs">
                  <span className="text-[11px] font-medium text-emerald-700 uppercase tracking-wider block">
                    Page Approved
                  </span>
                  <span className="text-lg font-bold text-emerald-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumApproved)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-green-50 shadow-2xs">
                  <span className="text-[11px] font-medium text-green-700 uppercase tracking-wider block">
                    Page Paid
                  </span>
                  <span className="text-lg font-bold text-green-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumPaid)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-amber-50 shadow-2xs">
                  <span className="text-[11px] font-medium text-amber-700 uppercase tracking-wider block">
                    Page Outstanding
                  </span>
                  <span className="text-lg font-bold text-amber-800 mt-0.5 block tabular-nums">
                    {formatCurrency(sumOutstanding)}
                  </span>
                </div>
                <div className="bg-white p-2.5 rounded-xl border border-purple-50 shadow-2xs">
                  <span className="text-[11px] font-medium text-purple-700 uppercase tracking-wider block">
                    Approval Rate
                  </span>
                  <span className="text-lg font-bold text-purple-800 mt-0.5 block tabular-nums">
                    {overallApprovalRate.toFixed(1)}%
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Controls Bar: Tab Switcher + Search Input */}
        <div className="bg-white border-b border-gray-100 px-6 py-2 flex flex-wrap items-center justify-between gap-3 shrink-0">
          {/* View Tab Switcher */}
          <div className="flex items-center gap-1 bg-gray-100 p-0.5 rounded-lg text-xs font-medium text-gray-600">
            <button
              onClick={() => setActiveTab('focused')}
              className={`px-3 py-1 rounded-md transition-all ${
                activeTab === 'focused'
                  ? 'bg-white text-indigo-700 font-semibold shadow-xs'
                  : 'hover:text-gray-900'
              }`}
            >
              🎯 {viewMode === 'billed' ? 'Billing Focus' : viewMode === 'approved' ? 'Approval Focus' : viewMode === 'paid' ? 'Payment & Settlement' : viewMode === 'tat' ? 'TAT Focus' : viewMode === 'outstanding' ? 'Ageing & Outstanding' : 'Metric View'}
            </button>
            <button
              onClick={() => setActiveTab('financials')}
              className={`px-3 py-1 rounded-md transition-all ${
                activeTab === 'financials'
                  ? 'bg-white text-indigo-700 font-semibold shadow-xs'
                  : 'hover:text-gray-900'
              }`}
            >
              💰 Financials
            </button>
            <button
              onClick={() => setActiveTab('timeline')}
              className={`px-3 py-1 rounded-md transition-all ${
                activeTab === 'timeline'
                  ? 'bg-white text-indigo-700 font-semibold shadow-xs'
                  : 'hover:text-gray-900'
              }`}
            >
              ⏱️ Timelines & TAT
            </button>
            <button
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1 rounded-md transition-all ${
                activeTab === 'all'
                  ? 'bg-white text-indigo-700 font-semibold shadow-xs'
                  : 'hover:text-gray-900'
              }`}
            >
              📋 All Details
            </button>
          </div>

          {/* Quick Search */}
          <div className="relative w-64 max-w-full">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg pl-8 pr-3 py-1 text-xs placeholder-gray-400 focus:outline-none focus:bg-white focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 shadow-2xs"
              placeholder="Search patient, ref ID, insurer…"
              value={search}
              onChange={(e) => {
                setSearch(e.target.value)
                setPage(1)
              }}
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X size={12} />
              </button>
            )}
          </div>
        </div>

        {/* Dynamic Table Content */}
        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="py-24 flex items-center justify-center">
              <Spinner />
            </div>
          ) : items.length === 0 ? (
            <div className="py-20 flex flex-col items-center justify-center text-center px-4">
              <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center text-gray-400 mb-3">
                <FileSpreadsheet size={24} />
              </div>
              <h3 className="text-sm font-semibold text-gray-800">No matching claims found</h3>
              <p className="text-xs text-gray-500 mt-1 max-w-sm">
                No records match the current filter selection or search criteria.
              </p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-gray-50 sticky top-0 z-10 border-b border-gray-200 shadow-2xs">
                <tr>
                  <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                    HSK Ref
                  </th>
                  <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                    Patient Name
                  </th>

                  {/* FOCUSED VIEW - BILLED */}
                  {activeTab === 'focused' && viewMode === 'billed' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                        Admission
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Procedure
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Preauth Req.
                      </th>
                      <th className="py-2.5 px-3 font-bold text-blue-700 bg-blue-50/70 uppercase tracking-wider tabular-nums text-right whitespace-nowrap">
                        Final Billed ★
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Discount
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Patient Paid
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - APPROVED / APPROVAL RATE */}
                  {activeTab === 'focused' && (viewMode === 'approved' || viewMode === 'approval_rate') && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / TPA
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Billed Amt
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Preauth Appr.
                      </th>
                      <th className="py-2.5 px-3 font-bold text-emerald-700 bg-emerald-50/70 uppercase tracking-wider tabular-nums text-right whitespace-nowrap">
                        Final Approved ★
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Approval %
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-rose-600 uppercase tracking-wider tabular-nums text-right">
                        Disallowed
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - PAID */}
                  {activeTab === 'focused' && viewMode === 'paid' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / Payer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-emerald-700 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-700 uppercase tracking-wider tabular-nums text-right">
                        Settled Amt
                      </th>
                      <th className="py-2.5 px-3 font-bold text-green-700 bg-green-50/70 uppercase tracking-wider tabular-nums text-right whitespace-nowrap">
                        Payment Received ★
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-purple-700 uppercase tracking-wider tabular-nums text-right">
                        TDS
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                        Payment Date
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        UTR No.
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Mode
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - OUTSTANDING / AGEING */}
                  {activeTab === 'focused' && (viewMode === 'outstanding' || viewMode === 'ageing') && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / Payer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-green-700 uppercase tracking-wider tabular-nums text-right">
                        Paid Amt
                      </th>
                      <th className="py-2.5 px-3 font-bold text-amber-700 bg-amber-50/70 uppercase tracking-wider tabular-nums text-right whitespace-nowrap">
                        Outstanding Balance ★
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Ageing Days
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Bucket
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Submission Status
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - TAT */}
                  {activeTab === 'focused' && viewMode === 'tat' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / Payer
                      </th>
                      <th className="py-2.5 px-3 font-bold text-purple-700 bg-purple-50/70 uppercase tracking-wider text-center whitespace-nowrap">
                        {tatStage ? `${tatStage.toUpperCase()} TAT` : 'Stage TAT'} ★
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Preauth TAT
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Discharge TAT
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Submission TAT
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Payment TAT
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - PAYER */}
                  {activeTab === 'focused' && viewMode === 'payer' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Payer Type
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / TPA
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Billed
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-emerald-700 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-green-700 uppercase tracking-wider tabular-nums text-right">
                        Paid
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-amber-700 uppercase tracking-wider tabular-nums text-right">
                        Outstanding
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Approval %
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - DISALLOWANCE */}
                  {activeTab === 'focused' && viewMode === 'disallowance' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / Payer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Billed
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-emerald-700 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-bold text-rose-700 bg-rose-50/70 uppercase tracking-wider tabular-nums text-right whitespace-nowrap">
                        Disallowed ★
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-rose-600 uppercase tracking-wider tabular-nums text-right">
                        Deductions
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Denial Reason / Category
                      </th>
                    </>
                  )}

                  {/* FOCUSED VIEW - OVERVIEW / STATUS */}
                  {activeTab === 'focused' && (viewMode === 'overview' || viewMode === 'status') && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                        Admission
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer / Payer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Billed
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-emerald-700 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-green-700 uppercase tracking-wider tabular-nums text-right">
                        Paid
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-amber-700 uppercase tracking-wider tabular-nums text-right">
                        Outstanding
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        Ageing
                      </th>
                    </>
                  )}

                  {/* FINANCIALS TAB */}
                  {activeTab === 'financials' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-blue-700 uppercase tracking-wider tabular-nums text-right">
                        Billed
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-emerald-700 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-rose-600 uppercase tracking-wider tabular-nums text-right">
                        Disallowed
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-green-700 uppercase tracking-wider tabular-nums text-right">
                        Paid
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-purple-700 uppercase tracking-wider tabular-nums text-right">
                        TDS
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-amber-700 uppercase tracking-wider tabular-nums text-right">
                        Outstanding
                      </th>
                    </>
                  )}

                  {/* TIMELINE TAB */}
                  {activeTab === 'timeline' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                        Admission Date
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                        Discharge Date
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                        LOS
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-purple-700 uppercase tracking-wider text-center">
                        Preauth TAT
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-purple-700 uppercase tracking-wider text-center">
                        Discharge TAT
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-purple-700 uppercase tracking-wider text-center">
                        Submission TAT
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-purple-700 uppercase tracking-wider text-center">
                        Payment TAT
                      </th>
                    </>
                  )}

                  {/* ALL DETAILS TAB */}
                  {activeTab === 'all' && (
                    <>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider whitespace-nowrap">
                        Admission
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        Insurer
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Billed
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Approved
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Paid
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider tabular-nums text-right">
                        Outstanding
                      </th>
                      <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                        UTR No.
                      </th>
                    </>
                  )}

                  <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="py-2.5 px-3 font-semibold text-gray-600 uppercase tracking-wider text-center">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((claim) => {
                  const billedVal = claim.final_claimed_amt ? parseFloat(claim.final_claimed_amt) : 0
                  const apprvVal = claim.final_bill_approved_amt ? parseFloat(claim.final_bill_approved_amt) : 0
                  const apprvRate = billedVal > 0 ? (apprvVal / billedVal) * 100 : 0

                  return (
                    <tr
                      key={claim.id}
                      onClick={() => navigate(`/claims/${claim.id}`)}
                      className="hover:bg-indigo-50/70 cursor-pointer transition-colors group"
                    >
                      <td className="py-2.5 px-3 font-mono text-gray-700 whitespace-nowrap font-medium">
                        {claim.hsk_ref_id ?? '—'}
                      </td>
                      <td className="py-2.5 px-3 font-medium text-gray-900 max-w-[150px] truncate">
                        {claim.patient_name ?? '—'}
                      </td>

                      {/* FOCUSED VIEW - BILLED */}
                      {activeTab === 'focused' && viewMode === 'billed' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-500 whitespace-nowrap">
                            {formatDate(claim.date_admission)}
                          </td>
                          <td className="py-2.5 px-3 text-gray-700 max-w-[140px] truncate">
                            {claim.procedure_name ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-700 text-right">
                            {formatCurrency(claim.preauth_requested_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-blue-800 font-bold bg-blue-50/50 text-right">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-600 text-right">
                            {formatCurrency(claim.hospital_discount)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-600 text-right">
                            {formatCurrency(claim.patient_paid_amt)}
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - APPROVED / APPROVAL RATE */}
                      {activeTab === 'focused' && (viewMode === 'approved' || viewMode === 'approval_rate') && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[140px] truncate">
                            {claim.insurer_name ?? claim.tpa_name ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-700 text-right">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-700 text-right">
                            {formatCurrency(claim.preauth_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-800 font-bold bg-emerald-50/50 text-right">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            <span
                              className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-semibold tabular-nums ${
                                apprvRate >= 80
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : apprvRate >= 50
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-rose-100 text-rose-800'
                              }`}
                            >
                              {apprvRate.toFixed(1)}%
                            </span>
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-rose-700 text-right font-medium">
                            {formatCurrency(claim.disallowed_amt)}
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - PAID */}
                      {activeTab === 'focused' && viewMode === 'paid' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-700 text-right font-medium">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-700 text-right">
                            {formatCurrency(claim.settled_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-green-800 font-bold bg-green-50/50 text-right">
                            {formatCurrency(claim.payment_received_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-purple-700 text-right font-medium">
                            {formatCurrency(claim.tds_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-gray-500 whitespace-nowrap">
                            {formatDate(claim.payment_received_date)}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-[11px] text-gray-700 max-w-[140px] truncate" title={claim.utr_no ?? ''}>
                            {claim.utr_no ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            <span className="px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 text-[10px] font-medium">
                              {claim.payment_mode ?? 'NEFT'}
                            </span>
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - OUTSTANDING / AGEING */}
                      {activeTab === 'focused' && (viewMode === 'outstanding' || viewMode === 'ageing') && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-700 text-right">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-green-700 text-right">
                            {formatCurrency(claim.payment_received_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-amber-800 font-bold bg-amber-50/50 text-right">
                            {formatCurrency(claim.outstanding_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums font-medium text-gray-800">
                            {claim.ageing_days !== null && claim.ageing_days !== undefined ? `${claim.ageing_days}d` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-semibold">
                              {claim.ageing_bucket ?? '—'}
                            </span>
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.submission_status ?? claim.submission_type ?? '—'}
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - TAT */}
                      {activeTab === 'focused' && viewMode === 'tat' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 text-center font-bold text-purple-900 bg-purple-50/50 tabular-nums">
                            {tatStage === 'preauth'
                              ? formatDays(claim.preauth_tat)
                              : tatStage === 'discharge'
                              ? formatDays(claim.discharge_tat)
                              : tatStage === 'submission'
                              ? formatDays(claim.submission_tat)
                              : tatStage === 'payment'
                              ? formatDays(claim.payment_tat)
                              : tatStage === 'query'
                              ? formatDays(claim.query_resolution_tat)
                              : formatDays(claim.preauth_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-gray-600">
                            {formatDays(claim.preauth_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-gray-600">
                            {formatDays(claim.discharge_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-gray-600">
                            {formatDays(claim.submission_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-gray-600">
                            {formatDays(claim.payment_tat)}
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - PAYER */}
                      {activeTab === 'focused' && viewMode === 'payer' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-700 font-medium whitespace-nowrap">
                            {claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.insurer_name ?? claim.tpa_name ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-700 text-right">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-700 text-right font-medium">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-green-700 text-right font-medium">
                            {formatCurrency(claim.payment_received_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-amber-700 text-right font-medium">
                            {formatCurrency(claim.outstanding_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums font-semibold">
                            {apprvRate.toFixed(1)}%
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - DISALLOWANCE */}
                      {activeTab === 'focused' && viewMode === 'disallowance' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600">
                            <div className="font-medium text-gray-800">{claim.insurer_name ?? '—'}</div>
                            {claim.payer_type && <div className="text-[11px] text-gray-400">{claim.payer_type}</div>}
                          </td>
                          <td className="py-2.5 px-3 text-right tabular-nums text-gray-600">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-right tabular-nums text-emerald-700 font-medium">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-right tabular-nums font-bold text-rose-700 bg-rose-50/40">
                            {formatCurrency(claim.disallowed_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-right tabular-nums text-rose-600 font-medium">
                            {formatCurrency(claim.deduction_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-gray-700 text-xs">
                            {claim.denial_reason ? (
                              <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-100 font-medium">
                                {claim.denial_reason}
                              </span>
                            ) : (
                              <span className="text-gray-400">Standard deductions</span>
                            )}
                          </td>
                        </>
                      )}

                      {/* FOCUSED VIEW - OVERVIEW / STATUS */}
                      {activeTab === 'focused' && (viewMode === 'overview' || viewMode === 'status') && (
                        <>
                          <td className="py-2.5 px-3 text-gray-500 whitespace-nowrap">
                            {formatDate(claim.date_admission)}
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[130px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-900 font-medium text-right">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-700 font-medium text-right">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-green-700 font-medium text-right">
                            {formatCurrency(claim.payment_received_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-amber-700 font-medium text-right">
                            {formatCurrency(claim.outstanding_amt)}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            {claim.ageing_bucket ? (
                              <span className="inline-block px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 text-[10px] font-medium">
                                {claim.ageing_bucket}
                              </span>
                            ) : (
                              <span className="text-gray-300">—</span>
                            )}
                          </td>
                        </>
                      )}

                      {/* FINANCIALS TAB */}
                      {activeTab === 'financials' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[120px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-blue-700 font-medium text-right">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-700 font-medium text-right">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-rose-700 text-right">
                            {formatCurrency(claim.disallowed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-green-700 font-medium text-right">
                            {formatCurrency(claim.payment_received_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-purple-700 text-right">
                            {formatCurrency(claim.tds_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-amber-700 font-medium text-right">
                            {formatCurrency(claim.outstanding_amt)}
                          </td>
                        </>
                      )}

                      {/* TIMELINE TAB */}
                      {activeTab === 'timeline' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-600 whitespace-nowrap">
                            {formatDate(claim.date_admission)}
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 whitespace-nowrap">
                            {formatDate(claim.date_discharge)}
                          </td>
                          <td className="py-2.5 px-3 text-center font-medium text-gray-700">
                            {claim.los_days !== null ? `${claim.los_days}d` : '—'}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-purple-800 font-medium">
                            {formatDays(claim.preauth_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-purple-800 font-medium">
                            {formatDays(claim.discharge_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-purple-800 font-medium">
                            {formatDays(claim.submission_tat)}
                          </td>
                          <td className="py-2.5 px-3 text-center tabular-nums text-purple-800 font-medium">
                            {formatDays(claim.payment_tat)}
                          </td>
                        </>
                      )}

                      {/* ALL DETAILS TAB */}
                      {activeTab === 'all' && (
                        <>
                          <td className="py-2.5 px-3 text-gray-500 whitespace-nowrap">
                            {formatDate(claim.date_admission)}
                          </td>
                          <td className="py-2.5 px-3 text-gray-600 max-w-[120px] truncate">
                            {claim.insurer_name ?? claim.payer_type ?? '—'}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-gray-900 text-right">
                            {formatCurrency(claim.final_claimed_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-emerald-700 text-right">
                            {formatCurrency(claim.final_bill_approved_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-green-700 text-right">
                            {formatCurrency(claim.payment_received_amt)}
                          </td>
                          <td className="py-2.5 px-3 tabular-nums text-amber-700 text-right">
                            {formatCurrency(claim.outstanding_amt)}
                          </td>
                          <td className="py-2.5 px-3 font-mono text-[10px] text-gray-600 max-w-[110px] truncate">
                            {claim.utr_no ?? '—'}
                          </td>
                        </>
                      )}

                      <td className="py-2.5 px-3 whitespace-nowrap">
                        <Badge label={claim.final_claim_status} />
                      </td>
                      <td className="py-2.5 px-3 text-center whitespace-nowrap">
                        <span className="text-indigo-600 group-hover:text-indigo-800 font-medium flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          View <ArrowRight size={12} />
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer & Pagination */}
        <div className="px-6 py-3 border-t border-gray-100 bg-white flex items-center justify-between shrink-0">
          <p className="text-xs text-gray-500">
            {data ? (
              <>
                Showing <span className="font-medium text-gray-700">{items.length}</span> of{' '}
                <span className="font-medium text-gray-700">{data.total}</span> claims
                {data.pages > 1 && ` (Page ${data.page} of ${data.pages})`}
              </>
            ) : (
              '—'
            )}
          </p>

          {data && data.pages > 1 && (
            <div className="flex items-center gap-1.5">
              <button
                className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1 disabled:opacity-40"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                <ChevronLeft size={13} />
                <span>Prev</span>
              </button>
              <div className="text-xs font-medium text-gray-600 px-2">
                {page} / {data.pages}
              </div>
              <button
                className="btn-secondary py-1 px-2.5 text-xs flex items-center gap-1 disabled:opacity-40"
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page >= data.pages}
              >
                <span>Next</span>
                <ChevronRight size={13} />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
