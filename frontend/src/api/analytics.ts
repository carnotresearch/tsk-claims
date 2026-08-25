import api from './client'
import type {
  KPIs,
  TATStats,
  OperationalTATRow,
  AgeingBucket,
  AgeingByPayerRow,
  DisallowanceReasonRow,
  StatusSnapshotResponse,
  PayerPerformance,
  MonthlyTrend,
  MonthlyDetailedStats,
  StatusBreakdown,
} from '../types'

const scope = (hospitalId?: number) => hospitalId ? `?hospital_id=${hospitalId}` : ''

export const getKPIs = async (hospitalId?: number): Promise<KPIs> =>
  (await api.get<KPIs>(`/analytics/kpis${scope(hospitalId)}`)).data

export const getTAT = async (hospitalId?: number): Promise<TATStats> =>
  (await api.get<TATStats>(`/analytics/tat${scope(hospitalId)}`)).data

export const getTATDetailed = async (hospitalId?: number): Promise<OperationalTATRow[]> =>
  (await api.get<OperationalTATRow[]>(`/analytics/tat-detailed${scope(hospitalId)}`)).data

export const getAgeing = async (hospitalId?: number): Promise<AgeingBucket[]> =>
  (await api.get<AgeingBucket[]>(`/analytics/ageing${scope(hospitalId)}`)).data

export const getAgeingByPayer = async (hospitalId?: number): Promise<AgeingByPayerRow[]> =>
  (await api.get<AgeingByPayerRow[]>(`/analytics/ageing-by-payer${scope(hospitalId)}`)).data

export const getTopDisallowances = async (hospitalId?: number): Promise<DisallowanceReasonRow[]> =>
  (await api.get<DisallowanceReasonRow[]>(`/analytics/top-disallowances${scope(hospitalId)}`)).data

export const getStatusSnapshot = async (hospitalId?: number): Promise<StatusSnapshotResponse> =>
  (await api.get<StatusSnapshotResponse>(`/analytics/status-snapshot${scope(hospitalId)}`)).data

export const getPayerPerformance = async (hospitalId?: number): Promise<PayerPerformance[]> =>
  (await api.get<PayerPerformance[]>(`/analytics/payer-performance${scope(hospitalId)}`)).data

export const getMonthly = async (hospitalId?: number): Promise<MonthlyTrend[]> =>
  (await api.get<MonthlyTrend[]>(`/analytics/monthly${scope(hospitalId)}`)).data

export const getMonthlyDetailed = async (hospitalId?: number): Promise<MonthlyDetailedStats[]> =>
  (await api.get<MonthlyDetailedStats[]>(`/analytics/monthly-detailed${scope(hospitalId)}`)).data

export const getStatusBreakdown = async (hospitalId?: number): Promise<StatusBreakdown[]> =>
  (await api.get<StatusBreakdown[]>(`/analytics/status-breakdown${scope(hospitalId)}`)).data
