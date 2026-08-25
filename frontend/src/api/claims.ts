import api from './client'
import type { ClaimListResponse, ClaimDetail } from '../types'

export interface ClaimFilters {
  page?: number
  page_size?: number
  status?: string
  insurer?: string
  payer_type?: string
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
