import { LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/auth'

interface Props {
  title: string
}

export default function TopBar({ title }: Props) {
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
      <h1 className="text-lg font-semibold text-gray-800">{title}</h1>
      <button onClick={handleLogout} className="btn-secondary text-xs py-1.5 px-3">
        <LogOut size={14} />
        Logout
      </button>
    </header>
  )
}
