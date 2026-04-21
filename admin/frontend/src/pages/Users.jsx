import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight } from 'lucide-react'
import api from '../api/axios'
import Badge from '../components/Badge'

const LEVELS = { 1: 'Start', 2: 'Return', 3: 'Base', 4: 'Stability' }
const STATUS_LABELS = { active: 'Активен', pending: 'Ожидает' }

function formatDate(d) {
  if (!d) return '—'
  const s = typeof d === 'string' ? d.split('T')[0] : d
  const [y, m, day] = String(s).split('-')
  return `${day}.${m}.${y}`
}

function Avatar({ name }) {
  const initials = (name || '?')
    .split(' ')
    .map(w => w[0])
    .slice(0, 2)
    .join('')
    .toUpperCase()
  return (
    <div className="w-9 h-9 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center text-xs font-semibold shrink-0">
      {initials}
    </div>
  )
}

function SkeletonRow() {
  return (
    <tr className="border-b border-gray-100">
      {Array.from({ length: 7 }).map((_, j) => (
        <td key={j} className="px-4 py-3">
          <div className="h-4 bg-gray-100 rounded animate-pulse w-24" />
        </td>
      ))}
    </tr>
  )
}

export default function Users() {
  const navigate = useNavigate()
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [level, setLevel] = useState('')
  const [page, setPage] = useState(1)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 25 }
      if (search) params.search = search
      if (status) params.status = status
      if (level) params.level = level
      const { data: res } = await api.get('/users', { params })
      setData(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [page, search, status, level])

  useEffect(() => { load() }, [load])

  function handleSearch(e) {
    setSearch(e.target.value)
    setPage(1)
  }

  function displayName(u) {
    if (u.full_name) return u.full_name
    return [u.last_name, u.first_name].filter(Boolean).join(' ') || `ID ${u.telegram_id}`
  }

  return (
    <div>
      <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Пользователи</h1>
        <span className="text-sm text-gray-500">Всего: {data.total}</span>
      </div>

      <div className="flex gap-3 mb-4">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={handleSearch}
            placeholder="Поиск по имени..."
            className="pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 w-64"
          />
        </div>
        <select
          value={status}
          onChange={e => { setStatus(e.target.value); setPage(1) }}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white"
        >
          <option value="">Все статусы</option>
          <option value="active">Активен</option>
          <option value="pending">Ожидает</option>
        </select>
        <select
          value={level}
          onChange={e => { setLevel(e.target.value); setPage(1) }}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white"
        >
          <option value="">Все уровни</option>
          {Object.entries(LEVELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {['Пользователь', 'Уровень', 'Статус', 'День', 'Старт', 'Повторов', 'Создан'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} />)
              : data.items.length === 0
                ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-14 text-center">
                      <div className="flex flex-col items-center gap-2 text-gray-400">
                        <Search size={28} strokeWidth={1.5} />
                        <span className="text-sm">Пользователи не найдены</span>
                      </div>
                    </td>
                  </tr>
                )
                : data.items.map(u => (
                  <tr
                    key={u.telegram_id}
                    className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/users/${u.telegram_id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <Avatar name={displayName(u)} />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{displayName(u)}</div>
                          <div className="text-xs text-gray-400">{u.telegram_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {u.level ? <Badge value="default" label={LEVELS[u.level]} /> : '—'}
                    </td>
                    <td className="px-4 py-3">
                      {u.status ? <Badge value={u.status} label={STATUS_LABELS[u.status] || u.status} /> : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {u.current_day != null ? `${u.current_day} / 28` : '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {u.program_start_date ? formatDate(u.program_start_date) : (
                        <span className="text-gray-400">Не назначен</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {u.week_repeat_count ?? '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      {formatDate(u.created_at)}
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">
            Страница {data.page} из {data.pages}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage(p => p - 1)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={14} /> Назад
            </button>
            <button
              disabled={page === data.pages}
              onClick={() => setPage(p => p + 1)}
              className="flex items-center gap-1 px-3 py-1.5 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Вперёд <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
