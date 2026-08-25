export interface User {
  id: number
  email: string
  full_name: string | null
  role: 'admin' | 'hospital_user'
  hospital_id: number | null
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface KPIs {
  total_claims: number
  total_billed: string
  total_approved: string
  total_settled: string
  total_paid: string
  total_outstanding: string
  total_deductions: string
  total_tds: string
  approval_rate: number
  collection_rate: number
}

export interface TATStats {
  preauth_avg_days: number | null
  discharge_avg_days: number | null
  submission_avg_days: number | null
  payment_avg_days: number | null
  query_resolution_avg_days: number | null
}

export interface OperationalTATRow {
  metric: string
  stage: string
  average: number
  fastest: number
  slowest: number
  target: number
  status: string
}

export interface AgeingBucket {
  bucket: string
  claim_count: number
  outstanding_amt: string
}

export interface AgeingByPayerRow {
  payer_type: string
  bucket_0_30: string
  bucket_31_60: string
  bucket_61_90: string
  bucket_90_plus: string
  total_outstanding: string
}

export interface DisallowanceReasonRow {
  reason: string
  cases_count: number
  disallowed_amt: string
}

export interface StatusSnapshotItem {
  status: string
  count: number
}

export interface StatusSnapshotResponse {
  preauth_statuses: StatusSnapshotItem[]
  discharge_statuses: StatusSnapshotItem[]
  submission_statuses: StatusSnapshotItem[]
}

export interface PayerPerformance {
  payer_type: string
  claim_count: number
  total_billed: string
  total_approved: string
  total_settled: string
  total_paid: string
  total_outstanding: string
  approval_rate: number
  deduction_rate: number
  collection_rate: number
}

export interface MonthlyTrend {
  month: string
  claim_count: number
  total_billed: string
  total_approved: string
  total_paid: string
}

export interface MonthlyDetailedStats {
  month: string
  claim_count: number
  total_billed: string
  total_approved: string
  total_paid: string
  total_tds: string
  total_outstanding: string
  patient_paid: string
  approval_rate: number
  paid_rate: number
  net_collected_rate: number
  tds_rate: number
  variance: string
}

export interface StatusBreakdown {
  status: string
  count: number
}

export interface ClaimSummary {
  id: number
  hospital_id: number
  hsk_ref_id: string | null
  month_label: string | null
  patient_name: string | null
  date_admission: string | null
  date_discharge: string | null
  los_days: number | null
  procedure_name?: string | null
  payer_type: string | null
  insurer_name: string | null
  tpa_name?: string | null
  policy_no?: string | null

  // Financials
  preauth_requested_amt?: string | null
  preauth_approved_amt?: string | null
  final_claimed_amt: string | null
  final_bill_approved_amt: string | null
  hospital_discount?: string | null
  patient_paid_amt?: string | null
  disallowed_amt?: string | null
  settled_amt?: string | null
  payment_received_amt: string | null
  tds_amt?: string | null
  deduction_amt?: string | null
  outstanding_amt: string | null

  // Settlement & TATs
  utr_no?: string | null
  payment_mode?: string | null
  payment_received_date?: string | null
  preauth_tat?: number | null
  discharge_tat?: number | null
  submission_tat?: number | null
  payment_tat?: number | null
  query_resolution_tat?: number | null

  // Ageing & Status
  ageing_days?: number | null
  ageing_bucket: string | null
  final_claim_status: string | null
  submission_type?: string | null
  submission_status?: string | null
  denial_reason?: string | null
  hospital_remarks?: string | null
}

export interface ClaimListResponse {
  items: ClaimSummary[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface ClaimDetail extends ClaimSummary {
  ihx_ref_id: string | null
  uhid: string | null
  patient_contact: string | null
  insured_name: string | null
  employee_code: string | null
  corporate_name: string | null
  procedure_name: string | null
  diagnosis: string | null
  tpa_name: string | null
  policy_no: string | null
  policy_type: string | null
  preauth_no: string | null
  preauth_request_date: string | null
  preauth_approval_date: string | null
  preauth_requested_amt: string | null
  preauth_approved_amt: string | null
  preauth_copay: string | null
  preauth_status: string | null
  preauth_tat: number | null
  final_bill_request_date: string | null
  final_bill_approval_date: string | null
  hospital_discount: string | null
  patient_paid_amt: string | null
  discharge_status: string | null
  discharge_tat: number | null
  submission_type: string | null
  submission_date: string | null
  submission_tat: number | null
  submission_status: string | null
  query_raised: boolean | null
  query_raised_date: string | null
  query_reason: string | null
  query_response_date: string | null
  query_resolution_tat: number | null
  settlement_date: string | null
  settled_amt: string | null
  tds_amt: string | null
  deduction_amt: string | null
  utr_no: string | null
  payment_received_date: string | null
  payment_mode: string | null
  payment_tat: number | null
  ageing_days: number | null
  denial_reason: string | null
  insurer_comments: string | null
  hospital_remarks: string | null
  created_at: string
  updated_at: string
}

export interface ChatSession {
  id: number
  user_id: number
  title: string | null
  created_at: string
}

export interface ChatMessage {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  sql_generated: string | null
  result_rows: Record<string, unknown>[] | null
  created_at: string
}

export interface SyncLog {
  id: number
  source_type: string
  source_path: string
  triggered_by: string
  synced_at: string
  rows_processed: number
  rows_inserted: number
  rows_updated: number
  rows_skipped: number
  rows_errored: number
  status: string
  error_details: string | null
}
