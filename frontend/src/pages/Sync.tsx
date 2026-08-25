import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Upload, CheckCircle, XCircle, RefreshCw, Server } from 'lucide-react'
import { uploadFile, getSyncLogs, triggerSync, getServerFileStatus } from '../api/sync'
import type { SyncResult } from '../api/sync'
import { formatDate } from '../lib/format'
import Spinner from '../components/ui/Spinner'
import { useAuthStore } from '../store/auth'

export default function Sync() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [result, setResult] = useState<SyncResult | null>(null)
  const [triggerResult, setTriggerResult] = useState<SyncResult | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const user = useAuthStore((s) => s.user)
  const isAdmin = user?.role === 'admin'

  const logsQ = useQuery({ queryKey: ['sync-logs'], queryFn: () => getSyncLogs(20) })
  const serverFileQ = useQuery({
    queryKey: ['server-file-status'],
    queryFn: getServerFileStatus,
    enabled: isAdmin,
  })

  const upload = useMutation({
    mutationFn: (file: File) => uploadFile(file),
    onSuccess: (data) => {
      setResult(data)
      qc.invalidateQueries({ queryKey: ['sync-logs'] })
      qc.invalidateQueries({ queryKey: ['server-file-status'] })
    },
  })

  const trigger = useMutation({
    mutationFn: triggerSync,
    onSuccess: (data) => {
      setTriggerResult(data)
      qc.invalidateQueries({ queryKey: ['sync-logs'] })
    },
  })

  const handleFile = (file: File | null) => {
    if (!file) return
    setResult(null)
    upload.mutate(file)
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Admin: Sync from Server File */}
      {isAdmin && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <Server size={20} className="text-indigo-500" />
            <h2 className="text-sm font-semibold text-gray-700">Sync from Server File</h2>
          </div>
          {serverFileQ.isLoading ? <Spinner /> : serverFileQ.data?.exists ? (
            <div className="flex items-center justify-between bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-3">
              <div>
                <p className="text-sm font-medium text-indigo-800">{serverFileQ.data.path}</p>
                <p className="text-xs text-indigo-500 mt-0.5">
                  {serverFileQ.data.size_bytes !== undefined && `${(serverFileQ.data.size_bytes / 1024).toFixed(1)} KB`}
                  {serverFileQ.data.modified_at && ` · Last modified ${formatDate(serverFileQ.data.modified_at)}`}
                </p>
              </div>
              <button
                className="btn-primary text-sm flex items-center gap-2"
                onClick={() => { setTriggerResult(null); trigger.mutate() }}
                disabled={trigger.isPending}
              >
                {trigger.isPending
                  ? <><RefreshCw size={14} className="animate-spin" /> Running…</>
                  : <><RefreshCw size={14} /> Run Sync</>
                }
              </button>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No Excel file found on server. Upload a file below to make it available for future server-side syncs.</p>
          )}
          {trigger.isError && (
            <div className="mt-3 flex items-center gap-2 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">
              <XCircle size={16} /> Sync failed. Check that the file exists on the server.
            </div>
          )}
          {triggerResult && (
            <SyncResultCard result={triggerResult} />
          )}
        </div>
      )}

      {/* Upload Card */}
      <div className="card">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Upload Excel File</h2>
        <div
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer ${
            dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-200 hover:border-indigo-300'
          }`}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0] ?? null) }}
        >
          <Upload size={32} className="mx-auto text-gray-300 mb-3" />
          <p className="text-sm font-medium text-gray-600">Drop your .xlsx file here</p>
          <p className="text-xs text-gray-400 mt-1">or click to browse</p>
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.xlsm"
            className="hidden"
            onChange={(e) => handleFile(e.target.files?.[0] ?? null)}
          />
        </div>

        {upload.isPending && (
          <div className="mt-4 flex items-center gap-3 text-sm text-gray-600">
            <RefreshCw size={16} className="animate-spin text-indigo-500" />
            Uploading and syncing…
          </div>
        )}

        {upload.isError && (
          <div className="mt-4 flex items-center gap-2 text-sm text-red-600 bg-red-50 px-4 py-3 rounded-lg">
            <XCircle size={16} />
            Upload failed. Please check the file and try again.
          </div>
        )}

        {result && <SyncResultCard result={result} />}
      </div>

      {/* Sync Logs */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Sync History</h2>
          <button className="text-xs text-indigo-600 hover:text-indigo-800" onClick={() => qc.invalidateQueries({ queryKey: ['sync-logs'] })}>
            Refresh
          </button>
        </div>
        {logsQ.isLoading ? <Spinner /> : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Date', 'Source', 'Status', 'Processed', 'Inserted', 'Skipped', 'Errors'].map(h => (
                  <th key={h} className="text-left py-2 px-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {logsQ.data?.map(log => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="py-2.5 px-3 text-xs text-gray-500 whitespace-nowrap">{formatDate(log.synced_at)}</td>
                  <td className="py-2.5 px-3 text-xs text-gray-700 max-w-[140px] truncate" title={log.source_path}>{log.source_path}</td>
                  <td className="py-2.5 px-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${log.status === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {log.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-xs text-gray-600">{log.rows_processed}</td>
                  <td className="py-2.5 px-3 text-xs text-green-700 font-medium">{log.rows_inserted}</td>
                  <td className="py-2.5 px-3 text-xs text-yellow-700">{log.rows_skipped}</td>
                  <td className="py-2.5 px-3 text-xs text-red-600">{log.rows_errored}</td>
                </tr>
              ))}
              {logsQ.data?.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-400 text-sm">No sync history yet</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

function SyncResultCard({ result }: { result: SyncResult }) {
  const ok = result.status === 'success'
  return (
    <div className={`mt-4 p-4 rounded-xl border ${ok ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
      <div className="flex items-center gap-2 mb-3">
        {ok ? <CheckCircle size={18} className="text-green-600" /> : <XCircle size={18} className="text-red-600" />}
        <span className={`font-semibold text-sm ${ok ? 'text-green-700' : 'text-red-700'}`}>
          Sync {ok ? 'Successful' : 'Failed'} — {result.source}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Processed', val: result.rows_processed, color: 'text-gray-700' },
          { label: 'Inserted', val: result.rows_inserted, color: 'text-green-700' },
          { label: 'Skipped', val: result.rows_skipped, color: 'text-yellow-700' },
          { label: 'Errors', val: result.rows_errored, color: 'text-red-700' },
        ].map(({ label, val, color }) => (
          <div key={label} className="text-center">
            <p className={`text-2xl font-bold ${color}`}>{val}</p>
            <p className="text-xs text-gray-500">{label}</p>
          </div>
        ))}
      </div>
      {result.errors.length > 0 && (
        <div className="mt-3 text-xs text-red-600 space-y-1">
          {result.errors.map((e, i) => <p key={i}>• {e}</p>)}
        </div>
      )}
    </div>
  )
}
