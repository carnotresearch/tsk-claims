import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import TopBar from './TopBar'
import { useEffect } from 'react'
import { useAuthStore } from '../../store/auth'
import { getMe } from '../../api/auth'

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/claims': 'Claims',
  '/chat': 'Ask AI',
  '/users': 'Users',
  '/sync': 'Sync',
}

export default function Layout() {
  const location = useLocation()
  const { setUser, token, user } = useAuthStore()

  // Load /me once on mount if we have a token but no user
  useEffect(() => {
    if (token && !user) {
      getMe().then(setUser).catch(() => {})
    }
  }, [token, user, setUser])

  const title =
    Object.entries(PAGE_TITLES).find(([k]) => location.pathname.startsWith(k))?.[1] ?? 'HSK Claims'

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar title={title} />
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
