import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { getClaim } from '../api/claims'
import { formatCurrency, formatDate, formatDays } from '../lib/format'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

const Field = ({ label, value }: { label: string; value: React.ReactNode }) => (
  <div>
    <dt className="text-xs text-gray-500 font-medium uppercase tracking-wide">{label}</dt>
    <dd className="mt-0.5 text-sm text-gray-800">{value || '—'}</dd>
  </div>
)

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
  <div className="card">
    <h3 className="text-sm font-semibold text-gray-700 mb-4 pb-2 border-b border-gray-100">{title}</h3>
    <dl className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">{children}</dl>
  </div>
)

export default function ClaimDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: claim, isLoading } = useQuery({
    queryKey: ['claim', id],
    queryFn: () => getClaim(Number(id)),
    enabled: !!id,
  })

  if (isLoading) return <Spinner />
  if (!claim) return <div className="card text-gray-500">Claim not found.</div>

  return (
    <div className="space-y-4 max-w-5xl">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate(-1)} className="btn-secondary text-xs py-1.5 px-3">
          <ArrowLeft size={14} /> Back
        </button>
        <div>
          <h1 className="text-lg font-bold text-gray-900">{claim.patient_name ?? 'Unknown Patient'}</h1>
          <p className="text-sm text-gray-500">HSK Ref: {claim.hsk_ref_id ?? '—'} · {claim.month_label ?? ''}</p>
        </div>
        <div className="ml-auto">
          <Badge label={claim.final_claim_status} />
        </div>
      </div>

      <Section title="Patient Information">
        <Field label="Patient Name" value={claim.patient_name} />
        <Field label="Insured Name" value={claim.insured_name} />
        <Field label="UHID" value={claim.uhid} />
        <Field label="Contact" value={claim.patient_contact} />
        <Field label="Employee Code" value={claim.employee_code} />
        <Field label="Corporate" value={claim.corporate_name} />
      </Section>

      <Section title="Admission & Stay">
        <Field label="Admission Date" value={formatDate(claim.date_admission)} />
        <Field label="Discharge Date" value={formatDate(claim.date_discharge)} />
        <Field label="LOS (Days)" value={claim.los_days} />
        <Field label="Procedure" value={claim.procedure_name} />
        <Field label="Diagnosis" value={claim.diagnosis} />
      </Section>

      <Section title="Payer & Policy">
        <Field label="Payer Type" value={claim.payer_type} />
        <Field label="TPA" value={claim.tpa_name} />
        <Field label="Insurer" value={claim.insurer_name} />
        <Field label="Policy No." value={claim.policy_no} />
        <Field label="Policy Type" value={claim.policy_type} />
      </Section>

      <Section title="Pre-authorisation">
        <Field label="Preauth No." value={claim.preauth_no} />
        <Field label="Request Date" value={formatDate(claim.preauth_request_date)} />
        <Field label="Approval Date" value={formatDate(claim.preauth_approval_date)} />
        <Field label="Requested Amt" value={formatCurrency(claim.preauth_requested_amt)} />
        <Field label="Approved Amt" value={formatCurrency(claim.preauth_approved_amt)} />
        <Field label="TAT" value={formatDays(claim.preauth_tat)} />
        <Field label="Status" value={claim.preauth_status} />
      </Section>

      <Section title="Final Bill & Discharge">
        <Field label="Billed Amount" value={formatCurrency(claim.final_claimed_amt)} />
        <Field label="Approved Amount" value={formatCurrency(claim.final_bill_approved_amt)} />
        <Field label="Hospital Discount" value={formatCurrency(claim.hospital_discount)} />
        <Field label="Patient Paid" value={formatCurrency(claim.patient_paid_amt)} />
        <Field label="Discharge Status" value={claim.discharge_status} />
        <Field label="Discharge TAT" value={formatDays(claim.discharge_tat)} />
        <Field label="Request Date" value={formatDate(claim.final_bill_request_date)} />
        <Field label="Approval Date" value={formatDate(claim.final_bill_approval_date)} />
      </Section>

      <Section title="Submission">
        <Field label="Submission Type" value={claim.submission_type} />
        <Field label="Submission Date" value={formatDate(claim.submission_date)} />
        <Field label="Submission TAT" value={formatDays(claim.submission_tat)} />
        <Field label="Status" value={claim.submission_status} />
      </Section>

      <Section title="Settlement & Payment">
        <Field label="Settlement Date" value={formatDate(claim.settlement_date)} />
        <Field label="Settled Amount" value={formatCurrency(claim.settled_amt)} />
        <Field label="TDS" value={formatCurrency(claim.tds_amt)} />
        <Field label="Deduction" value={formatCurrency(claim.deduction_amt)} />
        <Field label="UTR No." value={claim.utr_no} />
        <Field label="Payment Date" value={formatDate(claim.payment_received_date)} />
        <Field label="Payment Amount" value={formatCurrency(claim.payment_received_amt)} />
        <Field label="Payment Mode" value={claim.payment_mode} />
        <Field label="Payment TAT" value={formatDays(claim.payment_tat)} />
        <Field label="Outstanding" value={formatCurrency(claim.outstanding_amt)} />
        <Field label="Ageing Days" value={claim.ageing_days} />
        <Field label="Ageing Bucket" value={claim.ageing_bucket} />
      </Section>

      {(claim.denial_reason || claim.insurer_comments || claim.hospital_remarks) && (
        <Section title="Remarks & Notes">
          <Field label="Denial Reason" value={claim.denial_reason} />
          <Field label="Insurer Comments" value={claim.insurer_comments} />
          <Field label="Hospital Remarks" value={claim.hospital_remarks} />
        </Section>
      )}
    </div>
  )
}
