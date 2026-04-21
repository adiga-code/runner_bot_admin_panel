import { NavLink, useNavigate } from 'react-router-dom'
import { Activity, Users, BarChart2, Dumbbell, LogOut } from 'lucide-react'

const navItems = [
  { to: '/users', icon: Users, label: 'Пользователи' },
  { to: '/analytics', icon: BarChart2, label: 'Аналитика' },
  { to: '/workouts', icon: Dumbbell, label: 'Тренировки' },
]

export default function Sidebar() {
  const navigate = useNavigate()

  function handleLogout() {
    localStorage.removeItem('token')
    navigate('/login')
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
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-violet-50 text-violet-600'
                  : 'text-gray-600 hover:bg-gray-100'
              }`
            }
          >
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
