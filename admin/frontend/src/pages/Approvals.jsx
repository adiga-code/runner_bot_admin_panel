import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, RefreshCw } from 'lucide-react'
import api from '../api/axios'
import { useToast } from '../components/Toast'

const LEVELS    = { 1:'Start', 2:'Return', 3:'Base', 4:'Stability', 5:'Performance' }
const WELLBEING = { 1:'😞 Плохо', 2:'😤 Тяжело', 3:'😐 Норм', 4:'😊 Хорошо', 5:'🤩 Отлично' }
const SLEEP     = { 1:'😴 Плохо', 2:'💤 Норм', 3:'✨ Хорошо' }
const PAIN      = { 1:'✅ Нет', 2:'⚠️ Немного', 3:'🛑 Есть' }
const STRESS    = { 1:'✅ Нет', 2:'😐 Умеренный', 3:'😰 Сильный' }

const VERSIONS = [
  { value: 'base',     label: 'Base' },
  { value: 'light',    label: 'Light' },
  { value: 'recovery', label: 'Recovery' },
  { value: 'rest',     label: 'Отдых' },
]

function ApprovalCard({ item, onApproved }) {
  const toast = useToast()
  const navigate = useNavigate()
  const [version, setVersion] = useState('base')
  const [saving, setSaving] = useState(false)

  async function approve() {
    setSaving(true)
    try {
      const res = await api.post(`/users/${item.user_id}/approve-checkin?version=${version}`)
      const suffix = res.data.sent_telegram ? '' : ' (Telegram не настроен — задайте BOT_TOKEN)'
      toast(`✅ Одобрено: ${item.user_name}${suffix}`)
      onApproved(item.user_id)
    } catch (e) {
      toast(e?.response?.data?.detail || 'Ошибка отправки', 'error')
    }
    setSaving(false)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-start justify-between mb-4">
        <div>
          <button
            onClick={() => navigate(`/users/${item.user_id}`)}
            className="text-base font-semibold text-gray-900 hover:text-violet-600 transition-colors text-left"
          >
            {item.user_name}
          </button>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {item.level && (
              <span className="text-xs bg-violet-50 text-violet-700 px-2 py-0.5 rounded-full font-medium">
                L{item.level} {LEVELS[item.level]}
              </span>
            )}
            {item.is_new_logic ? (
              <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                New Logic · {item.current_period}
              </span>
            ) : (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-medium">
                Old Logic
              </span>
            )}
            {item.planned_minutes > 0 && (
              <span className="text-xs text-gray-500">{item.planned_minutes} мин план</span>
            )}
          </div>
        </div>
        {item.checkin_at && (
          <span className="text-xs text-gray-400 shrink-0">
            {new Date(item.checkin_at).toLocaleTimeString('ru', { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      <div className="grid grid-cols-4 gap-2 mb-4">
        {[
          ['Самочувствие', WELLBEING[item.wellbeing]],
          ['Сон',          SLEEP[item.sleep_quality]],
          ['Боль',         PAIN[item.pain_level]],
          ['Стресс',       STRESS[item.stress_level]],
        ].map(([label, val]) => (
          <div key={label} className="bg-gray-50 rounded-lg p-2.5 text-center">
            <div className="text-xs text-gray-500 mb-1">{label}</div>
            <div className="text-sm font-medium">{val || '—'}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-2 mb-4">
        {VERSIONS.map(v => (
          <button
            key={v.value}
            onClick={() => setVersion(v.value)}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium border transition-colors ${
              version === v.value
                ? 'border-violet-400 bg-violet-50 text-violet-700'
                : 'border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {v.label}
          </button>
        ))}
      </div>

      <button
        onClick={approve}
        disabled={saving}
        className="w-full bg-violet-600 text-white py-2.5 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors disabled:opacity-60 flex items-center justify-center gap-2"
      >
        <CheckCircle size={16} />
        {saving ? 'Отправляем...' : 'Одобрить и отправить тренировку'}
      </button>
    </div>
  )
}

export default function Approvals() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.get('/pending-checkins')
      setItems(Array.isArray(res.data) ? res.data : [])
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  function onApproved(userId) {
    setItems(prev => prev.filter(i => i.user_id !== userId))
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
          <h1 className="text-xl font-semibold text-gray-900">Одобрение чек-инов</h1>
          <p className="text-sm text-gray-500 mt-1">Ожидают отправки тренировки сегодня</p>
        </div>
        <button
          onClick={load}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <RefreshCw size={15} />
          Обновить
        </button>
      </div>

      {items.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <div className="text-4xl mb-3">✅</div>
          <p className="text-gray-500 text-sm">Все чек-ины обработаны</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {items.map(item => (
            <ApprovalCard key={item.user_id} item={item} onApproved={onApproved} />
          ))}
        </div>
      )}
    </div>
  )
}
