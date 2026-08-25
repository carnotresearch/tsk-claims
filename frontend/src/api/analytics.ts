import api from './client'
import type { KPIs, TATStats, AgeingBucket, PayerPerformance, MonthlyTrend, StatusBreakdown } from '../types'

const scope = (hospitalId?: number) => hospitalId ? `?hospital_id=${hospitalId}` : ''

export const getKPIs = async (hospitalId?: number): Promise<KPIs> =>
  (await api.get<KPIs>(`/analytics/kpis${scope(hospitalId)}`)).data

export const getTAT = async (hospitalId?: number): Promise<TATStats> =>
  (await api.get<TATStats>(`/analytics/tat${scope(hospitalId)}`)).data

export const getAgeing = async (hospitalId?: number): Promise<AgeingBucket[]> =>
  (await api.get<AgeingBucket[]>(`/analytics/ageing${scope(hospitalId)}`)).data

export const getPayerPerformance = async (hospitalId?: number): Promise<PayerPerformance[]> =>
  (await api.get<PayerPerformance[]>(`/analytics/payer-performance${scope(hospitalId)}`)).data

export const getMonthly = async (hospitalId?: number): Promise<MonthlyTrend[]> =>
  (await api.get<MonthlyTrend[]>(`/analytics/monthly${scope(hospitalId)}`)).data

export const getStatusBreakdown = async (hospitalId?: number): Promise<StatusBreakdown[]> =>
  (await api.get<StatusBreakdown[]>(`/analytics/status-breakdown${scope(hospitalId)}`)).data
