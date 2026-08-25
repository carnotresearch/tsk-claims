import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, UserCheck, UserX } from 'lucide-react'
import { getUsers, createUser, deactivateUser } from '../api/users'
import { getHospitals } from '../api/hospitals'
import type { User } from '../types'
import Spinner from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

function AddUserModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'hospital_user' as 'hospital_user' | 'admin',
    hospital_id: '' as string,
  })
  const [error, setError] = useState('')

  const hospitalsQ = useQuery({
    queryKey: ['hospitals'],
    queryFn: getHospitals,
    staleTime: 0, // always fresh — new hospitals appear after Excel upload
  })

  const create = useMutation({
    mutationFn: () => createUser({
      ...form,
      hospital_id: form.hospital_id ? Number(form.hospital_id) : undefined,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['users'] }); onClose() },
    onError: (e: unknown) =>
      setError((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ?? 'Failed to create user'),
  })

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-5">Create New User</h2>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input className="input" placeholder="user@hospital.com" value={form.email} onChange={e => set('email', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" className="input" value={form.password} onChange={e => set('password', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name (optional)</label>
            <input className="input" value={form.full_name} onChange={e => set('full_name', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
            <select className="input" value={form.role} onChange={e => { set('role', e.target.value); set('hospital_id', '') }}>
              <option value="hospital_user">Hospital User</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {form.role === 'hospital_user' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Hospital</label>
              {hospitalsQ.isLoading ? (
                <div className="input flex items-center text-gray-400 text-sm">Loading hospitals…</div>
              ) : (
                <select
                  className="input"
                  value={form.hospital_id}
                  onChange={e => set('hospital_id', e.target.value)}
                >
                  <option value="">— Select hospital —</option>
                  {hospitalsQ.data?.map(h => (
                    <option key={h.id} value={h.id}>{h.name}</option>
                  ))}
                </select>
              )}
              {hospitalsQ.data?.length === 0 && (
                <p className="text-xs text-amber-600 mt-1">No hospitals found. Upload an Excel file first to populate hospitals.</p>
              )}
            </div>
          )}
          {error && <p className="text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
        </div>
        <div className="flex gap-2 mt-6">
          <button className="btn-secondary flex-1" onClick={onClose}>Cancel</button>
          <button
            className="btn-primary flex-1"
            onClick={() => create.mutate()}
            disabled={create.isPending || (form.role === 'hospital_user' && !form.hospital_id)}
          >
            {create.isPending ? 'Creating…' : 'Create User'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Users() {
  const qc = useQueryClient()
  const [showModal, setShowModal] = useState(false)

  const { data: users, isLoading } = useQuery({ queryKey: ['users'], queryFn: getUsers })
  const { data: hospitals } = useQuery({ queryKey: ['hospitals'], queryFn: getHospitals, staleTime: 0 })

  // Build id → name lookup for the table
  const hospitalName = (id: number | null) =>
    id == null ? '—' : (hospitals?.find(h => h.id === id)?.name ?? `ID ${id}`)

  const deactivate = useMutation({
    mutationFn: (id: number) => deactivateUser(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  return (
    <div className="space-y-4 max-w-4xl">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">{users?.length ?? 0} user(s) total</p>
        <button className="btn-primary text-sm" onClick={() => setShowModal(true)}>
          <Plus size={15} /> Add User
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? <Spinner /> : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                {['Email', 'Name', 'Role', 'Hospital', 'Status', ''].map(h => (
                  <th key={h} className="text-left py-2.5 px-4 text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users?.map((u: User) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="py-3 px-4 text-gray-800 font-medium">{u.email}</td>
                  <td className="py-3 px-4 text-gray-600">{u.full_name ?? '—'}</td>
                  <td className="py-3 px-4">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                      {u.role.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-600 text-sm">{hospitalName(u.hospital_id)}</td>
                  <td className="py-3 px-4">
                    <Badge label={u.is_active ? 'Active' : 'Inactive'} />
                  </td>
                  <td className="py-3 px-4 text-right">
                    {u.is_active ? (
                      <button
                        onClick={() => { if (confirm(`Deactivate ${u.email}?`)) deactivate.mutate(u.id) }}
                        className="text-red-500 hover:text-red-700 p-1 rounded"
                        title="Deactivate"
                      >
                        <UserX size={15} />
                      </button>
                    ) : (
                      <UserCheck size={15} className="text-gray-300" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showModal && <AddUserModal onClose={() => setShowModal(false)} />}
    </div>
  )
}
