import api from './client'
import type { ClaimListResponse, ClaimDetail } from '../types'

export interface ClaimFilters {
  page?: number
  page_size?: number
  status?: string
  preauth_status?: string
  discharge_status?: string
  submission_status?: string
  disallowed_reason?: string
  has_disallowed?: boolean
  insurer?: string
  payer_type?: string
  month_label?: string
  has_outstanding?: boolean
  has_paid?: boolean
  has_approved?: boolean
  has_billed?: boolean
  tat_stage?: 'preauth' | 'discharge' | 'submission' | 'payment' | 'query'
  date_from?: string
  date_to?: string
  search?: string
  ageing_bucket?: string
}

export const getClaims = async (filters: ClaimFilters = {}): Promise<ClaimListResponse> => {
  const params = Object.fromEntries(
    Object.entries(filters).filter(([, v]) => v !== '' && v !== undefined),
  )
  return (await api.get<ClaimListResponse>('/claims', { params })).data
}

export const getClaim = async (id: number): Promise<ClaimDetail> =>
  (await api.get<ClaimDetail>(`/claims/${id}`)).data
