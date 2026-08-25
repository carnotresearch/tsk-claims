import api from './client'
import type { SyncLog } from '../types'

export interface SyncResult {
  status: string
  source: string
  rows_processed: number
  rows_inserted: number
  rows_updated: number
  rows_skipped: number
  rows_errored: number
  errors: string[]
}

export const uploadFile = async (file: File): Promise<SyncResult> => {
  const form = new FormData()
  form.append('file', file)
  return (await api.post<SyncResult>('/sync/upload', form)).data
}

export const getSyncLogs = async (limit = 20): Promise<SyncLog[]> =>
  (await api.get<SyncLog[]>(`/sync/logs?limit=${limit}`)).data

export const triggerSync = async (): Promise<SyncResult> =>
  (await api.post<SyncResult>('/sync/trigger')).data

export interface ServerFileStatus {
  exists: boolean
  path: string
  size_bytes?: number
  modified_at?: string
}

export const getServerFileStatus = async (): Promise<ServerFileStatus> =>
  (await api.get<ServerFileStatus>('/sync/server-file')).data
