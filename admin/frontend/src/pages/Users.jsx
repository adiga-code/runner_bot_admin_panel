import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ChevronLeft, ChevronRight, CheckSquare, Square, Minus } from 'lucide-react'
import api from '../api/axios'
import Badge from '../components/Badge'
import Modal from '../components/Modal'
import { useToast } from '../components/Toast'

const LEVELS = { 1: 'Start', 2: 'Return', 3: 'Base', 4: 'Stability', 5: 'Performance' }
const STATUS_LABELS = { active: 'Активен', pending: 'Ожидает', paused: 'Пауза' }
const PERIOD_LABELS = {
  base_in: 'Base-In', base: 'Base',
  preparatory: 'Prep', specialized: 'Spec',
  recovery_period: 'Recovery',
}

const BULK_ACTIONS = [
  { value: 'migrate_to_new_logic', label: 'Перевести на новую логику', needsDate: true,  color: 'violet' },
  { value: 'activate',             label: 'Активировать',              needsDate: true,  color: 'green'  },
  { value: 'pause',                label: 'Поставить на паузу',        needsDate: false, color: 'yellow' },
  { value: 'resume',               label: 'Возобновить',               needsDate: false, color: 'green'  },
]

function formatDate(d) {
  if (!d) return '—'
  const s = typeof d === 'string' ? d.split('T')[0] : d
  const [y, m, day] = String(s).split('-')
  return `${day}.${m}.${y}`
}

function Avatar({ name }) {
  const initials = (name || '?').split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
  return (
    <div className="w-9 h-9 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center text-xs font-semibold shrink-0">
      {initials}
    </div>
  )
}

function SortIcon({ col, sortBy, sortDir }) {
  if (sortBy !== col) return <span className="ml-1 text-gray-400 text-xs">⇅</span>
  return <span className="ml-1 text-violet-600 text-xs">{sortDir === 'asc' ? '↑' : '↓'}</span>
}

function SkeletonRow({ cols }) {
  return (
    <tr className="border-b border-gray-100">
      {Array.from({ length: cols }).map((_, j) => (
        <td key={j} className="px-4 py-3">
          <div className="h-4 bg-gray-100 rounded animate-pulse w-24" />
        </td>
      ))}
    </tr>
  )
}

function Checkbox({ checked, indeterminate, onChange, onClick }) {
  return (
    <button
      onClick={e => { e.stopPropagation(); onClick ? onClick(e) : onChange(e) }}
      className="text-violet-600 hover:text-violet-700 transition-colors"
    >
      {indeterminate
        ? <Minus size={17} className="text-violet-400" />
        : checked
          ? <CheckSquare size={17} />
          : <Square size={17} className="text-gray-300 hover:text-gray-400" />
      }
    </button>
  )
}

export default function Users() {
  const navigate = useNavigate()
  const toast = useToast()
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 1 })
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [level, setLevel] = useState('')
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('created_at')
  const [sortDir, setSortDir] = useState('desc')

  // selection
  const [selected, setSelected] = useState(new Set())

  // bulk action modal
  const [bulkModal, setBulkModal] = useState(false)
  const [bulkAction, setBulkAction] = useState('migrate_to_new_logic')
  const [bulkDate, setBulkDate] = useState('')
  const [bulkLoading, setBulkLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: 25, sort_by: sortBy, sort_dir: sortDir }
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
  }, [page, search, status, level, sortBy, sortDir])

  useEffect(() => { load() }, [load])
  // clear selection on page/filter change
  useEffect(() => { setSelected(new Set()) }, [page, search, status, level])

  function toggleSort(col) {
    if (sortBy === col) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(col)
      setSortDir('desc')
    }
    setPage(1)
  }

  function handleSearch(e) { setSearch(e.target.value); setPage(1) }

  function displayName(u) {
    if (u.full_name) return u.full_name
    return [u.last_name, u.first_name].filter(Boolean).join(' ') || `ID ${u.telegram_id}`
  }

  const pageIds = data.items.map(u => u.telegram_id)
  const allPageSelected = pageIds.length > 0 && pageIds.every(id => selected.has(id))
  const somePageSelected = pageIds.some(id => selected.has(id)) && !allPageSelected

  function toggleAll() {
    if (allPageSelected) {
      setSelected(prev => { const s = new Set(prev); pageIds.forEach(id => s.delete(id)); return s })
    } else {
      setSelected(prev => new Set([...prev, ...pageIds]))
    }
  }

  function toggleOne(id) {
    setSelected(prev => {
      const s = new Set(prev)
      s.has(id) ? s.delete(id) : s.add(id)
      return s
    })
  }

  async function runBulkAction() {
    const actionDef = BULK_ACTIONS.find(a => a.value === bulkAction)
    if (!actionDef) return
    setBulkLoading(true)
    try {
      const body = { user_ids: [...selected], action: bulkAction }
      if (actionDef.needsDate && bulkDate) body.start_date = bulkDate
      const { data: res } = await api.post('/users/bulk-action', body)
      const ok = res.ok?.length ?? 0
      const skipped = res.skipped?.length ?? 0
      const errors = res.errors?.length ?? 0
      toast(`Готово: ${ok} применено${skipped ? `, ${skipped} пропущено` : ''}${errors ? `, ${errors} ошибок` : ''}`)
      setSelected(new Set())
      setBulkModal(false)
      load()
    } catch {
      toast('Ошибка выполнения', 'error')
    }
    setBulkLoading(false)
  }

  const selectedAction = BULK_ACTIONS.find(a => a.value === bulkAction)

  return (
    <div className="pb-24">
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
          <option value="paused">Пауза</option>
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
              <th className="px-4 py-3 w-10">
                <Checkbox
                  checked={allPageSelected}
                  indeterminate={somePageSelected}
                  onClick={toggleAll}
                />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Пользователь</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700" onClick={() => toggleSort('level')}>
                Уровень<SortIcon col="level" sortBy={sortBy} sortDir={sortDir} />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700" onClick={() => toggleSort('status')}>
                Статус<SortIcon col="status" sortBy={sortBy} sortDir={sortDir} />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Прогресс</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700" onClick={() => toggleSort('program_start_date')}>
                Период / Старт<SortIcon col="program_start_date" sortBy={sortBy} sortDir={sortDir} />
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Повторов</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700" onClick={() => toggleSort('created_at')}>
                Создан<SortIcon col="created_at" sortBy={sortBy} sortDir={sortDir} />
              </th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 8 }).map((_, i) => <SkeletonRow key={i} cols={8} />)
              : data.items.length === 0
                ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-14 text-center">
                      <div className="flex flex-col items-center gap-2 text-gray-400">
                        <Search size={28} strokeWidth={1.5} />
                        <span className="text-sm">Пользователи не найдены</span>
                      </div>
                    </td>
                  </tr>
                )
                : data.items.map(u => {
                  const isSelected = selected.has(u.telegram_id)
                  return (
                    <tr
                      key={u.telegram_id}
                      className={`border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${isSelected ? 'bg-violet-50' : ''}`}
                      onClick={() => navigate(`/users/${u.telegram_id}`)}
                    >
                      <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                        <Checkbox checked={isSelected} onClick={() => toggleOne(u.telegram_id)} />
                      </td>
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
                        <div className="flex flex-col gap-1">
                          {u.level ? <Badge value="default" label={`L${u.level} ${LEVELS[u.level] || ''}`} /> : '—'}
                          {u.injury_return_active && (
                            <span className="inline-flex px-2 py-0.5 bg-orange-100 text-orange-700 rounded-full text-xs font-medium">Возврат</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-1">
                          {u.status ? <Badge value={u.status} label={STATUS_LABELS[u.status] || u.status} /> : '—'}
                          {u.status === 'pending' && (
                            u.onboarding_complete
                              ? <span className="inline-flex px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-xs font-medium">Готов к старту</span>
                              : <span className="inline-flex px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full text-xs font-medium">Анкета</span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {u.current_period
                          ? <span className="text-violet-600 font-medium">Нед.{u.program_week_number || '?'}</span>
                          : u.current_day != null ? `${u.current_day} / 28` : '—'
                        }
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {u.current_period
                          ? <span className="text-violet-500 text-xs">{PERIOD_LABELS[u.current_period] || u.current_period}</span>
                          : u.program_start_date ? formatDate(u.program_start_date) : (
                            <span className="text-gray-400">Не назначен</span>
                          )
                        }
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {u.current_period ? <span className="text-gray-300">—</span> : (u.week_repeat_count ?? '—')}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {formatDate(u.created_at)}
                      </td>
                    </tr>
                  )
                })
            }
          </tbody>
        </table>
      </div>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <span className="text-sm text-gray-500">Страница {data.page} из {data.pages}</span>
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

      {/* Floating bulk action bar */}
      {selected.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 bg-gray-900 text-white px-5 py-3 rounded-2xl shadow-2xl">
          <span className="text-sm font-medium">
            {selected.size} {selected.size === 1 ? 'пользователь' : selected.size < 5 ? 'пользователя' : 'пользователей'}
          </span>
          <div className="w-px h-5 bg-gray-700" />
          <button
            onClick={() => { setBulkAction('migrate_to_new_logic'); setBulkDate(''); setBulkModal(true) }}
            className="text-sm text-violet-300 hover:text-violet-200 transition-colors font-medium"
          >
            Новая логика
          </button>
          <button
            onClick={() => { setBulkAction('activate'); setBulkDate(''); setBulkModal(true) }}
            className="text-sm text-green-300 hover:text-green-200 transition-colors font-medium"
          >
            Активировать
          </button>
          <button
            onClick={() => { setBulkAction('pause'); setBulkModal(true) }}
            className="text-sm text-yellow-300 hover:text-yellow-200 transition-colors font-medium"
          >
            Пауза
          </button>
          <button
            onClick={() => { setBulkAction('resume'); setBulkModal(true) }}
            className="text-sm text-green-300 hover:text-green-200 transition-colors font-medium"
          >
            Возобновить
          </button>
          <div className="w-px h-5 bg-gray-700" />
          <button
            onClick={() => setSelected(new Set())}
            className="text-sm text-gray-400 hover:text-gray-300 transition-colors"
          >
            Отмена
          </button>
        </div>
      )}

      {/* Bulk action confirmation modal */}
      <Modal
        isOpen={bulkModal}
        onClose={() => setBulkModal(false)}
        title={selectedAction?.label || 'Действие'}
        footer={
          <>
            <button
              onClick={() => setBulkModal(false)}
              className="bg-white text-gray-700 border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              Отмена
            </button>
            <button
              onClick={runBulkAction}
              disabled={bulkLoading}
              className="bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors disabled:opacity-60"
            >
              {bulkLoading ? 'Применяется...' : `Применить к ${selected.size}`}
            </button>
          </>
        }
      >
        <p className="text-sm text-gray-600 mb-4">
          Действие будет применено к <b>{selected.size}</b> {selected.size === 1 ? 'пользователю' : 'пользователям'}.
        </p>

        {bulkAction === 'migrate_to_new_logic' && (
          <div className="text-sm text-gray-600 bg-violet-50 border border-violet-100 rounded-lg p-3 mb-4">
            Уровень (L1–L3), период, объём — будут пересчитаны по анкете.<br />
            Создаётся недельный план. Старые логи сохраняются.
          </div>
        )}

        {selectedAction?.needsDate && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Дата старта <span className="text-gray-400 font-normal">(необязательно — по умолчанию сегодня)</span>
            </label>
            <input
              type="date"
              value={bulkDate}
              onChange={e => setBulkDate(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
            <p className="text-xs text-gray-400 mt-1">
              Неделя начнётся с понедельника этой даты.
            </p>
          </div>
        )}
      </Modal>
    </div>
  )
}
