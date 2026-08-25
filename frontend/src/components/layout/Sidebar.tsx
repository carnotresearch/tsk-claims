import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  MessageSquare,
  Users,
  RefreshCw,
  Activity,
} from 'lucide-react'
import { useAuthStore } from '../../store/auth'

const nav = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/claims', icon: FileText, label: 'Claims' },
  { to: '/chat', icon: MessageSquare, label: 'Ask AI' },
  { to: '/sync', icon: RefreshCw, label: 'Sync' },
]

const adminNav = [
  { to: '/users', icon: Users, label: 'Users' },
]

export default function Sidebar() {
  const user = useAuthStore((s) => s.user)

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-indigo-600 text-white'
        : 'text-slate-300 hover:bg-slate-700 hover:text-white'
    }`

  return (
    <aside className="w-60 min-h-screen bg-slate-800 flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <Activity className="text-indigo-400" size={22} />
          <span className="text-white font-semibold text-lg leading-tight">HSK Claims</span>
        </div>
        <p className="text-slate-400 text-xs mt-0.5">Cashless Tracker</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={linkClass}>
            <Icon size={18} />
            {label}
          </NavLink>
        ))}

        {user?.role === 'admin' && (
          <>
            <div className="pt-4 pb-1 px-4">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Admin</p>
            </div>
            {adminNav.map(({ to, icon: Icon, label }) => (
              <NavLink key={to} to={to} className={linkClass}>
                <Icon size={18} />
                {label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* User info */}
      <div className="px-4 py-4 border-t border-slate-700">
        <p className="text-slate-300 text-sm font-medium truncate">{user?.full_name ?? user?.email}</p>
        <p className="text-slate-500 text-xs capitalize">{user?.role?.replace('_', ' ')}</p>
      </div>
    </aside>
  )
}
