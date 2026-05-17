import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { RefreshCw, UserCheck, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../api/axios'
import { useToast } from '../components/Toast'

const LEVELS = { 1: 'Start', 2: 'Return', 3: 'Base', 4: 'Stability', 5: 'Performance' }

const GOAL_LABELS = {
  start_zero: 'Начать бегать с нуля',
  return: 'Вернуться после перерыва',
  distance: 'Пробежать дистанцию',
  improve: 'Улучшить результат',
  no_pain: 'Бегать без боли',
  health: 'Здоровье и форма',
}

function today() {
  return new Date().toISOString().slice(0, 10)
}

function tomorrow() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return d.toISOString().slice(0, 10)
}

function InfoRow({ label, value }) {
  if (!value) return null
  return (
    <div className="flex gap-2 text-sm">
      <span className="text-gray-400 shrink-0 w-40">{label}</span>
      <span className="text-gray-700">{value}</span>
    </div>
  )
}

function PendingCard({ user, onDone }) {
  const toast = useToast()
  const navigate = useNavigate()

  const suggestedLevel = user.level || 1
  const [level, setLevel] = useState(suggestedLevel)
  const [startDate, setStartDate] = useState(today())
  const [expanded, setExpanded] = useState(false)
  const [saving, setSaving] = useState(false)

  async function handleAction(giveTrial) {
    setSaving(true)
    try {
      const res = await api.post(`/users/${user.telegram_id}/activate-with-access`, {
        level,
        start_date: startDate,
        give_trial: giveTrial,
      })
      const modeLabel = giveTrial ? 'Триал активирован' : 'Приглашение на оплату отправлено'
      const tgNote = res.data.sent_telegram ? '' : ' (Telegram не настроен)'
      toast(`✅ ${modeLabel}${tgNote}`)
      onDone(user.telegram_id)
    } catch (e) {
      toast(e?.response?.data?.detail || 'Ошибка', 'error')
    } finally {
      setSaving(false)
    }
  }

  const registeredAt = user.created_at
    ? new Date(user.created_at).toLocaleDateString('ru', { day: '2-digit', month: '2-digit', year: 'numeric' })
    : '—'

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <button
            onClick={() => navigate(`/users/${user.telegram_id}`)}
            className="text-base font-semibold text-gray-900 hover:text-violet-600 transition-colors text-left"
          >
            {user.full_name || `ID ${user.telegram_id}`}
          </button>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-xs bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded-full font-medium">
              ожидает одобрения
            </span>
            {user.city && (
              <span className="text-xs text-gray-400">{user.city}</span>
            )}
            <span className="text-xs text-gray-400">зарег. {registeredAt}</span>
          </div>
        </div>
      </div>

      {/* Questionnaire summary */}
      <div className="mb-4 space-y-1">
        <InfoRow label="Цель" value={GOAL_LABELS[user.q_goal] || user.q_goal} />
        <InfoRow label="Рекомендуемый уровень" value={user.level ? `L${user.level} — ${LEVELS[user.level]}` : '—'} />
      </div>

      {/* Expand questionnaire */}
      <button
        onClick={() => setExpanded(v => !v)}
        className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 mb-4 transition-colors"
      >
        {expanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {expanded ? 'Скрыть анкету' : 'Показать анкету'}
      </button>

      {expanded && (
        <div className="mb-4 space-y-1 border-t border-gray-100 pt-3">
          <InfoRow label="Бегает сейчас?" value={user.q_runs} />
          <InfoRow label="Частота" value={user.q_frequency} />
          <InfoRow label="Объём" value={user.q_volume} />
          <InfoRow label="Длинный забег" value={user.q_longest_run} />
          <InfoRow label="Перерыв?" value={user.q_break} />
          <InfoRow label="Длительность перерыва" value={user.q_break_duration} />
          <InfoRow label="Самооценка" value={user.q_self_level} />
          <InfoRow label="Боль" value={user.q_pain} />
          <InfoRow label="Травмы" value={user.q_injury_history} />
          <InfoRow label="Структура" value={user.q_structure} />
          <InfoRow label="Дистанция" value={user.q_distance} />
          <InfoRow label="Дата гонки" value={user.q_race_date} />
        </div>
      )}

      {/* Level selector */}
      <div className="mb-3">
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Уровень программы</label>
        <div className="flex gap-2">
          {Object.entries(LEVELS).map(([lvl, name]) => (
            <button
              key={lvl}
              onClick={() => setLevel(Number(lvl))}
              className={`flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                level === Number(lvl)
                  ? 'border-violet-400 bg-violet-50 text-violet-700'
                  : 'border-gray-200 text-gray-500 hover:bg-gray-50'
              }`}
            >
              L{lvl}<br />
              <span className="font-normal">{name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Start date */}
      <div className="mb-4">
        <label className="block text-xs font-medium text-gray-500 mb-1.5">Дата старта программы</label>
        <div className="flex gap-2">
          <button
            onClick={() => setStartDate(today())}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              startDate === today() ? 'border-violet-400 bg-violet-50 text-violet-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50'
            }`}
          >
            Сегодня
          </button>
          <button
            onClick={() => setStartDate(tomorrow())}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
              startDate === tomorrow() ? 'border-violet-400 bg-violet-50 text-violet-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50'
            }`}
          >
            Завтра
          </button>
          <input
            type="date"
            value={startDate}
            onChange={e => setStartDate(e.target.value)}
            className="flex-1 border border-gray-200 rounded-lg px-2 py-1.5 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-violet-400"
          />
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex gap-2">
        <button
          onClick={() => handleAction(true)}
          disabled={saving}
          className="flex-1 bg-violet-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
        >
          <UserCheck size={15} />
          {saving ? '...' : '🎁 Дать триал (10 дней)'}
        </button>
        <button
          onClick={() => handleAction(false)}
          disabled={saving}
          className="flex-1 bg-white border border-gray-300 text-gray-700 py-2.5 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors disabled:opacity-60"
        >
          {saving ? '...' : '💳 На оплату'}
        </button>
      </div>
    </div>
  )
}

export default function PendingUsers() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/users', { params: { status: 'pending', per_page: 100 } })
      const all = res.data.items || []
      setUsers(all.filter(u => u.onboarding_complete))
    } catch {
      setUsers([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  function onDone(userId) {
    setUsers(prev => prev.filter(u => u.telegram_id !== userId))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Заявки пользователей</h1>
          <p className="text-sm text-gray-500 mt-1">
            Прошли анкету, ожидают решения — {users.length} чел.
          </p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <RefreshCw size={15} />
          Обновить
        </button>
      </div>

      {users.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <div className="text-4xl mb-3">✅</div>
          <p className="text-gray-500 text-sm">Нет пользователей, ожидающих одобрения</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {users.map(u => (
            <PendingCard key={u.telegram_id} user={u} onDone={onDone} />
          ))}
        </div>
      )}
    </div>
  )
}
