import { useState, useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, Users, BarChart2, Dumbbell, LogOut, CheckSquare, BookOpen, FileText, Clock } from 'lucide-react'
import api from '../api/axios'

export default function Sidebar() {
  const navigate = useNavigate()
  const [checkinCount, setCheckinCount] = useState(0)
  const [pendingCount, setPendingCount] = useState(0)

  function fetchCounts() {
    api.get('/pending-checkins')
      .then(r => setCheckinCount(Array.isArray(r.data) ? r.data.length : 0))
      .catch(() => {})
    api.get('/users', { params: { status: 'pending', per_page: 1 } })
      .then(r => setPendingCount(r.data?.total || 0))
      .catch(() => {})
  }

  useEffect(() => {
    fetchCounts()
    const interval = setInterval(fetchCounts, 60_000)
    return () => clearInterval(interval)
  }, [])

  function handleLogout() {
    localStorage.removeItem('token')
    navigate('/login')
  }

  function navClass({ isActive }) {
    return `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
      isActive ? 'bg-violet-50 text-violet-600' : 'text-gray-600 hover:bg-gray-100'
    }`
  }

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-white border-r border-gray-200 flex flex-col z-10">
      <div className="px-6 py-5 flex items-center gap-2.5">
        <div className="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center">
          <Activity size={18} className="text-violet-600" />
        </div>
        <span className="text-lg font-bold text-violet-600">28 дней</span>
      </div>

      <nav className="px-3 mt-4 flex flex-col gap-1 flex-1">
        {/* Pending users (onboarding done, awaiting decision) */}
        <NavLink to="/pending" className={navClass}>
          <Clock size={17} />
          <span className="flex-1">Заявки</span>
          {pendingCount > 0 && (
            <span className="bg-yellow-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
              {pendingCount > 9 ? '9+' : pendingCount}
            </span>
          )}
        </NavLink>

        {/* Checkin approvals */}
        <NavLink to="/approvals" className={navClass}>
          <CheckSquare size={17} />
          <span className="flex-1">Чек-ины</span>
          {checkinCount > 0 && (
            <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
              {checkinCount > 9 ? '9+' : checkinCount}
            </span>
          )}
        </NavLink>

        {[
          { to: '/users',             icon: Users,     label: 'Пользователи' },
          { to: '/materials',         icon: FileText,  label: 'Материалы' },
          { to: '/analytics',         icon: BarChart2, label: 'Аналитика' },
          { to: '/workouts',          icon: Dumbbell,  label: 'Тренировки (28д)' },
          { to: '/workout-templates', icon: BookOpen,  label: 'Силовые шаблоны' },
        ].map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} className={navClass}>
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 pb-5">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2 w-full rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors"
        >
          <LogOut size={17} />
          Выйти
        </button>
      </div>
    </aside>
  )
}
