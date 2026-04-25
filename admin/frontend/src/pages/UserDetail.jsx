import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Flag, MoreVertical, ChevronDown, ChevronUp } from 'lucide-react'
import api from '../api/axios'
import Badge from '../components/Badge'
import Modal from '../components/Modal'
import { useToast } from '../components/Toast'

// ─── Dictionaries ────────────────────────────────────────────────────────────
const LEVELS      = { 1:'Start', 2:'Return', 3:'Base', 4:'Stability' }
const STATUS_LABELS = { active:'Активен', pending:'Ожидает' }
const WELLBEING   = { 1:'😞 Плохо', 2:'😤 Тяжеловато', 3:'😐 Нормально', 4:'😊 Хорошо', 5:'🤩 Отлично' }
const SLEEP       = { 1:'😴 Плохо', 2:'💤 Нормально', 3:'✨ Хорошо' }
const PAIN        = { 1:'✅ Нет', 2:'⚠️ Немного', 3:'🛑 Есть' }
const STRESS      = { 1:'✅ Нет', 2:'😐 Умеренный', 3:'😰 Сильный' }
const COMPLETION  = { done:'Выполнено', partial:'Частично', skipped:'Пропущено' }
const VERSION_LABELS = { base:'Base', light:'Light', recovery:'Recovery', rest:'Отдых' }
const DAY_TYPE    = { run:'🏃 Бег', strength:'💪 Силовая', recovery:'🔄 Восстановление', rest:'😴 Отдых' }
const GENDER      = { m:'Мужской', f:'Женский' }
const GOAL        = {
  start_zero:'Начать с нуля', return:'Вернуться после перерыва',
  distance:'Пробежать дистанцию', improve:'Улучшить результат',
  no_pain:'Бегать без боли', health:'Общее здоровье и форма',
}
const RUNS        = { no:'Нет', irregular:'Нерегулярно', regular:'Регулярно' }
const FREQUENCY   = { '0_1':'0–1 р/нед', '2_3':'2–3 р/нед', '4plus':'4+ р/нед' }
const VOLUME      = { to_10:'до 10 км', '10_25':'10–25 км', '25_50':'25–50 км', '50plus':'50+ км' }
const LONGEST     = { to_5:'до 5 км', '5_10':'5–10 км', '10_15':'10–15 км', '15plus':'15+ км' }
const EXPERIENCE  = { beginner:'Только начинаю', to_6m:'до 6 мес', '6_12m':'6–12 мес', '1_3y':'1–3 года', '3plus':'3+ лет' }
const BREAK_DUR   = { no:'Нет', to_1m:'до 1 мес', '1_3m':'1–3 мес', '3_6m':'3–6 мес', '6plus':'6+ мес' }
const RUN_FEEL    = { hard:'Тяжело', medium:'Нормально', easy:'Комфортно' }
const PAIN_LOC    = { knees:'Колени', feet:'Стопы', shin:'Голень', achilles:'Ахилл', back:'Спина', other:'Другое' }
const SPORTS      = { gym:'Зал', bike:'Велосипед', swim:'Плавание', other:'Другое', none:'Только бег' }
const STR_FREQ    = { no:'Не делаю', sometimes:'Иногда', regularly:'Регулярно' }
const SELF_LEVEL  = { beginner:'Новичок', base:'Базовый', medium:'Средний', advanced:'Продвинутый' }

// ─── Helpers ─────────────────────────────────────────────────────────────────
function formatDate(d) {
  if (!d) return '—'
  const s = typeof d === 'string' ? d.split('T')[0] : String(d)
  const [y, m, day] = s.split('-')
  return `${day}.${m}.${y}`
}

function calcAge(bd) {
  if (!bd) return null
  const birth = new Date(bd), today = new Date()
  let age = today.getFullYear() - birth.getFullYear()
  const dm = today.getMonth() - birth.getMonth()
  if (dm < 0 || (dm === 0 && today.getDate() < birth.getDate())) age--
  return age
}

function parseTags(str, dict) {
  if (!str) return []
  return str.split(',').map(s => dict[s.trim()] || s.trim())
}

// ─── Shared UI ────────────────────────────────────────────────────────────────
function InfoRow({ label, value }) {
  return (
    <div className="flex items-start py-2 border-b border-gray-100 last:border-0">
      <span className="text-sm text-gray-500 w-44 shrink-0">{label}</span>
      <span className="text-sm text-gray-900">{value || '—'}</span>
    </div>
  )
}

function Tag({ children }) {
  return (
    <span className="inline-flex px-2 py-0.5 bg-gray-100 text-gray-700 rounded-full text-xs font-medium mr-1 mb-1">
      {children}
    </span>
  )
}

function BtnPrimary({ children, onClick, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors disabled:opacity-60"
    >
      {children}
    </button>
  )
}

function BtnSecondary({ children, onClick }) {
  return (
    <button
      onClick={onClick}
      className="bg-white text-gray-700 border border-gray-200 px-4 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
    >
      {children}
    </button>
  )
}

// ─── Profile Tab ──────────────────────────────────────────────────────────────
function ProfileTab({ user }) {
  const age = calcAge(user.birth_date)
  const tz = user.timezone_offset != null
    ? `UTC${user.timezone_offset >= 0 ? '+' : ''}${user.timezone_offset}`
    : null

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-6">
        {/* Personal */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Личные данные</h3>
          <InfoRow label="Фамилия" value={user.last_name} />
          <InfoRow label="Имя" value={user.first_name} />
          <InfoRow label="Отчество" value={user.middle_name} />
          <InfoRow label="Пол" value={GENDER[user.gender]} />
          <InfoRow label="Дата рождения" value={
            user.birth_date
              ? `${formatDate(user.birth_date)}${age != null ? ` (${age} лет)` : ''}`
              : null
          } />
          <InfoRow label="Страна" value={user.country} />
          <InfoRow label="Город" value={user.city} />
          <InfoRow label="Район" value={user.district} />
          <InfoRow label="Часовой пояс" value={tz} />
        </div>

        {/* Program */}
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Программа</h3>
          <div className="flex items-start py-2 border-b border-gray-100">
            <span className="text-sm text-gray-500 w-44 shrink-0">Уровень</span>
            {user.level ? <Badge value="default" label={LEVELS[user.level]} /> : <span className="text-sm text-gray-900">—</span>}
          </div>
          <div className="flex items-start py-2 border-b border-gray-100">
            <span className="text-sm text-gray-500 w-44 shrink-0">Статус</span>
            {user.status ? <Badge value={user.status} label={STATUS_LABELS[user.status]} /> : <span className="text-sm text-gray-900">—</span>}
          </div>
          <InfoRow label="Дата старта" value={formatDate(user.program_start_date)} />
          <InfoRow label="Текущий день" value={
            user.program_start_date
              ? `${Math.max(1, Math.floor((Date.now() - new Date(user.program_start_date)) / 86400000) + 1)} / 28`
              : null
          } />
          <InfoRow label="Повторов недели" value={user.week_repeat_count} />
          <InfoRow label="Силовые" value={
            user.strength_format === 'gym' ? 'Зал' :
            user.strength_format === 'home' ? 'Дома' : null
          } />
          <InfoRow label="Зарегистрирован" value={formatDate(user.created_at)} />
        </div>
      </div>

      {/* Questionnaire */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-5">Анкета</h3>
        <div className="grid grid-cols-2 gap-x-10">
          <div>
            <SectionTitle>🎯 Цель</SectionTitle>
            <InfoRow label="Цель" value={GOAL[user.q_goal]} />

            <SectionTitle>🏃 Бег</SectionTitle>
            <InfoRow label="Бегает" value={RUNS[user.q_runs]} />
            <InfoRow label="Частота" value={FREQUENCY[user.q_frequency]} />
            <InfoRow label="Объём" value={VOLUME[user.q_volume]} />
            <InfoRow label="Самый длинный бег" value={LONGEST[user.q_longest_run]} />
            <InfoRow label="Как даётся" value={RUN_FEEL[user.q_run_feel]} />
            <InfoRow label="Структура" value={
              user.q_structure === 'yes' ? 'Есть' :
              user.q_structure === 'no' ? 'Нет' : null
            } />

            <SectionTitle>📅 Опыт</SectionTitle>
            <InfoRow label="Стаж" value={EXPERIENCE[user.q_experience]} />
            <InfoRow label="Перерыв" value={BREAK_DUR[user.q_break_duration]} />
          </div>

          <div>
            <SectionTitle>🦵 Здоровье</SectionTitle>
            <InfoRow label="Боль" value={
              user.q_pain === 'yes' ? 'Есть' :
              user.q_pain === 'no' ? 'Нет' :
              user.q_pain === 'little' ? 'Немного' : null
            } />
            <div className="flex items-start py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500 w-44 shrink-0">Локализация</span>
              <div className="flex flex-wrap">
                {parseTags(user.q_pain_location, PAIN_LOC).length
                  ? parseTags(user.q_pain_location, PAIN_LOC).map(t => <Tag key={t}>{t}</Tag>)
                  : <span className="text-sm text-gray-900">—</span>
                }
              </div>
            </div>
            <InfoRow label="Усиливается" value={
              user.q_pain_increases === 'yes' ? 'Да' :
              user.q_pain_increases === 'no' ? 'Нет' :
              user.q_pain_increases === 'not_sure' ? 'Не уверен' : null
            } />
            <InfoRow label="Травмы за год" value={
              user.q_injury_history === 'yes' ? 'Да' :
              user.q_injury_history === 'no' ? 'Нет' : null
            } />

            <SectionTitle>💪 Физическая форма</SectionTitle>
            <div className="flex items-start py-2 border-b border-gray-100">
              <span className="text-sm text-gray-500 w-44 shrink-0">Другой спорт</span>
              <div className="flex flex-wrap">
                {parseTags(user.q_other_sports, SPORTS).length
                  ? parseTags(user.q_other_sports, SPORTS).map(t => <Tag key={t}>{t}</Tag>)
                  : <span className="text-sm text-gray-900">—</span>
                }
              </div>
            </div>
            <InfoRow label="Силовые (частота)" value={STR_FREQ[user.q_strength_frequency]} />

            <SectionTitle>⭐ Самооценка</SectionTitle>
            <InfoRow label="Уровень" value={SELF_LEVEL[user.q_self_level]} />
          </div>
        </div>
      </div>
    </div>
  )
}

function SectionTitle({ children }) {
  return (
    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1 mt-5 first:mt-0">
      {children}
    </p>
  )
}

// ─── Progress Tab ─────────────────────────────────────────────────────────────
function ProgressTab({ logs, onReload }) {
  const toast = useToast()
  const done    = logs.filter(l => l.completion_status === 'done').length
  const skipped = logs.filter(l => l.completion_status === 'skipped').length

  let streak = 0
  for (const l of [...logs].reverse()) {
    if (l.completion_status === 'done') streak++
    else break
  }

  const weekAgo    = Date.now() - 7 * 86400000
  const weekLogs   = logs.filter(l => l.date && new Date(l.date) >= new Date(weekAgo))
  const weekDone   = weekLogs.filter(l => l.completion_status === 'done').length
  const weekPct    = weekLogs.length > 0 ? Math.round(weekDone / weekLogs.length * 100) : 0

  const [openMenu, setOpenMenu]     = useState(null)
  const [assignModal, setAssignModal] = useState(null)
  const [statusModal, setStatusModal] = useState(null)
  const [assignVersion, setAssignVersion] = useState('base')
  const [newStatus, setNewStatus]   = useState('done')
  const [saving, setSaving]         = useState(false)

  async function saveAssign() {
    setSaving(true)
    try {
      await api.put(`/logs/${assignModal.id}`, { assigned_version: assignVersion })
      toast('Версия тренировки обновлена')
      setAssignModal(null)
      onReload()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  async function saveStatus() {
    setSaving(true)
    try {
      await api.put(`/logs/${statusModal.id}/completion`, { completion_status: newStatus })
      toast('Статус обновлён')
      setStatusModal(null)
      onReload()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  return (
    <div>
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Выполнено', value: done },
          { label: 'Пропущено', value: skipped },
          { label: 'Серия дней', value: streak },
          { label: '% недели', value: `${weekPct}%` },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-gray-200 rounded-xl p-4">
            <div className="text-2xl font-bold text-gray-900">{value}</div>
            <div className="text-sm text-gray-500 mt-1">{label}</div>
          </div>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {['День','Дата','Тип','Версия','Самоч.','Сон','Боль','Стресс','Статус','Усилие','⚑',''].map(h => (
                <th key={h} className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {logs.length === 0
              ? <tr><td colSpan={12} className="px-4 py-10 text-center text-gray-400">Нет данных</td></tr>
              : logs.map(log => {
                const noCheckin = !log.checkin_done
                return (
                  <tr key={log.id} className={`border-b border-gray-100 ${noCheckin ? 'bg-gray-50/60' : 'hover:bg-gray-50'}`}>
                    <td className="px-3 py-2.5 text-gray-700">{log.calendar_day ?? log.day_index ?? '—'}</td>
                    <td className="px-3 py-2.5 text-gray-700">{formatDate(log.date)}</td>
                    <td className="px-3 py-2.5 text-gray-700">{log.workout ? DAY_TYPE[log.workout.day_type] : '—'}</td>
                    <td className="px-3 py-2.5">
                      {log.assigned_version
                        ? <Badge value={log.assigned_version} label={VERSION_LABELS[log.assigned_version]} />
                        : '—'}
                    </td>
                    <td className="px-3 py-2.5">{log.wellbeing ? WELLBEING[log.wellbeing]?.split(' ')[0] : '—'}</td>
                    <td className="px-3 py-2.5">{log.sleep_quality ? SLEEP[log.sleep_quality]?.split(' ')[0] : '—'}</td>
                    <td className="px-3 py-2.5">{log.pain_level ? PAIN[log.pain_level]?.split(' ')[0] : '—'}</td>
                    <td className="px-3 py-2.5">{log.stress_level ? STRESS[log.stress_level]?.split(' ')[0] : '—'}</td>
                    <td className="px-3 py-2.5">
                      {noCheckin
                        ? <span className="text-xs text-gray-400 italic">Чекин не выполнен</span>
                        : log.completion_status
                          ? <Badge value={log.completion_status} label={COMPLETION[log.completion_status]} />
                          : '—'
                      }
                    </td>
                    <td className="px-3 py-2.5 text-gray-700">{log.effort_level ? `${log.effort_level}/5` : '—'}</td>
                    <td className="px-3 py-2.5">
                      {log.red_flag && <Flag size={13} className="text-red-500" />}
                    </td>
                    <td className="px-3 py-2.5 relative">
                      <button
                        onClick={() => setOpenMenu(openMenu === log.id ? null : log.id)}
                        className="text-gray-400 hover:text-gray-600 p-0.5 rounded"
                      >
                        <MoreVertical size={14} />
                      </button>
                      {openMenu === log.id && (
                        <div className="absolute right-6 top-8 bg-white border border-gray-200 rounded-lg shadow-lg z-20 w-48 py-1">
                          <button
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                            onClick={() => { setAssignModal(log); setAssignVersion(log.assigned_version || 'base'); setOpenMenu(null) }}
                          >
                            Назначить тренировку
                          </button>
                          <button
                            className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                            onClick={() => { setStatusModal(log); setNewStatus(log.completion_status || 'done'); setOpenMenu(null) }}
                          >
                            Изменить статус
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                )
              })
            }
          </tbody>
        </table>
      </div>

      {/* Assign modal */}
      <Modal
        isOpen={!!assignModal}
        onClose={() => setAssignModal(null)}
        title={`День ${assignModal?.calendar_day ?? assignModal?.day_index ?? '?'} — ${formatDate(assignModal?.date)}`}
        footer={<><BtnSecondary onClick={() => setAssignModal(null)}>Отмена</BtnSecondary><BtnPrimary onClick={saveAssign} disabled={saving}>Сохранить</BtnPrimary></>}
      >
        <p className="text-sm text-gray-500 mb-4">Выберите версию тренировки:</p>
        <div className="flex flex-col gap-2.5">
          {['base','light','recovery','rest'].map(v => (
            <label key={v} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${assignVersion === v ? 'border-violet-300 bg-violet-50' : 'border-gray-200 hover:bg-gray-50'}`}>
              <input type="radio" name="av" value={v} checked={assignVersion === v} onChange={() => setAssignVersion(v)} className="accent-violet-600" />
              <Badge value={v} label={VERSION_LABELS[v]} />
            </label>
          ))}
        </div>
      </Modal>

      {/* Status modal */}
      <Modal
        isOpen={!!statusModal}
        onClose={() => setStatusModal(null)}
        title="Изменить статус выполнения"
        footer={<><BtnSecondary onClick={() => setStatusModal(null)}>Отмена</BtnSecondary><BtnPrimary onClick={saveStatus} disabled={saving}>Сохранить</BtnPrimary></>}
      >
        <div className="flex flex-col gap-2.5">
          {['done','partial','skipped'].map(s => (
            <label key={s} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${newStatus === s ? 'border-violet-300 bg-violet-50' : 'border-gray-200 hover:bg-gray-50'}`}>
              <input type="radio" name="cs" value={s} checked={newStatus === s} onChange={() => setNewStatus(s)} className="accent-violet-600" />
              <Badge value={s} label={COMPLETION[s]} />
            </label>
          ))}
        </div>
      </Modal>
    </div>
  )
}

// ─── Testing Tab ─────────────────────────────────────────────────────────────
function TestingTab({ userId, onReload }) {
  const toast = useToast()
  const [targetDay, setTargetDay]       = useState(1)
  const [deleteFromDay, setDeleteFromDay] = useState(1)
  const [saving, setSaving]             = useState(false)

  const [setDayModal, setSetDayModal]         = useState(false)
  const [deleteLogsModal, setDeleteLogsModal] = useState(false)
  const [resetModal, setResetModal]           = useState(false)
  const [onboardingModal, setOnboardingModal] = useState(false)

  async function doSetDay() {
    setSaving(true)
    try {
      await api.post(`/users/${userId}/set-day`, { day: targetDay })
      toast(`Пользователь переведён на день ${targetDay}`)
      setSetDayModal(false)
      onReload()
    } catch { toast('Ошибка', 'error') }
    setSaving(false)
  }

  async function doDeleteLogs() {
    setSaving(true)
    try {
      await api.delete(`/users/${userId}/logs?from_day=${deleteFromDay}`)
      toast(`Логи с дня ${deleteFromDay} удалены`)
      setDeleteLogsModal(false)
      onReload()
    } catch { toast('Ошибка', 'error') }
    setSaving(false)
  }

  async function doReset() {
    setSaving(true)
    try {
      await api.post(`/users/${userId}/reset`)
      toast('Прогресс сброшен до дня 1')
      setResetModal(false)
      onReload()
    } catch { toast('Ошибка', 'error') }
    setSaving(false)
  }

  async function doResetOnboarding() {
    setSaving(true)
    try {
      await api.post(`/users/${userId}/reset-onboarding`)
      toast('Онбординг и прогресс сброшены')
      setOnboardingModal(false)
      onReload()
    } catch { toast('Ошибка', 'error') }
    setSaving(false)
  }

  return (
    <div>
      <div className="bg-amber-50 border border-amber-200 rounded-xl px-5 py-3.5 mb-6 flex items-center gap-3">
        <span className="text-amber-500 text-base">⚠️</span>
        <p className="text-sm text-amber-700">Только для тестирования. Действия необратимы — реальные данные будут удалены.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* Set day */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Перейти на день X</h3>
          <p className="text-xs text-gray-500 mb-4">Меняет дату старта так, чтобы сегодня был выбранный день программы. Логи не затрагиваются.</p>
          <div className="flex items-center gap-3">
            <input
              type="number" min={1} max={35} value={targetDay}
              onChange={e => setTargetDay(Math.max(1, Math.min(35, +e.target.value)))}
              className="w-20 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
            <span className="text-sm text-gray-500">из 28</span>
            <BtnPrimary onClick={() => setSetDayModal(true)}>Применить</BtnPrimary>
          </div>
        </div>

        {/* Delete logs from day */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Удалить логи с дня X</h3>
          <p className="text-xs text-gray-500 mb-4">Удаляет все session_logs начиная с выбранного дня. Бот увидит пользователя как будто этих дней не было.</p>
          <div className="flex items-center gap-3">
            <input
              type="number" min={1} max={35} value={deleteFromDay}
              onChange={e => setDeleteFromDay(Math.max(1, Math.min(35, +e.target.value)))}
              className="w-20 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
            <span className="text-sm text-gray-500">и далее</span>
            <button
              onClick={() => setDeleteLogsModal(true)}
              className="bg-orange-100 text-orange-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-orange-200 transition-colors"
            >
              Удалить
            </button>
          </div>
        </div>

        {/* Full reset */}
        <div className="bg-white border border-red-100 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Полный сброс прогресса</h3>
          <p className="text-xs text-gray-500 mb-4">Удаляет все логи, устанавливает старт = сегодня (день 1), статус = active, повторы = 0. Анкета сохраняется.</p>
          <button
            onClick={() => setResetModal(true)}
            className="bg-red-100 text-red-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
          >
            Сбросить прогресс
          </button>
        </div>

        {/* Reset onboarding */}
        <div className="bg-white border border-red-100 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Сбросить онбординг</h3>
          <p className="text-xs text-gray-500 mb-4">Удаляет все логи и анкету. Статус → pending, уровень и дата старта очищаются. Бот запустит онбординг заново.</p>
          <button
            onClick={() => setOnboardingModal(true)}
            className="bg-red-100 text-red-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
          >
            Сбросить онбординг
          </button>
        </div>
      </div>

      <Modal
        isOpen={setDayModal} onClose={() => setSetDayModal(false)}
        title={`Перейти на день ${targetDay}?`}
        footer={<><BtnSecondary onClick={() => setSetDayModal(false)}>Отмена</BtnSecondary><BtnPrimary onClick={doSetDay} disabled={saving}>Применить</BtnPrimary></>}
      >
        <p className="text-sm text-gray-600">Дата старта будет пересчитана так, чтобы сегодня = день <b>{targetDay}</b>. Существующие логи не удаляются.</p>
      </Modal>

      <Modal
        isOpen={deleteLogsModal} onClose={() => setDeleteLogsModal(false)}
        title={`Удалить логи с дня ${deleteFromDay}?`}
        footer={<><BtnSecondary onClick={() => setDeleteLogsModal(false)}>Отмена</BtnSecondary><button onClick={doDeleteLogs} disabled={saving} className="bg-orange-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-orange-700 transition-colors disabled:opacity-60">Удалить</button></>}
      >
        <p className="text-sm text-gray-600">Все session_logs начиная с дня <b>{deleteFromDay}</b> будут безвозвратно удалены.</p>
      </Modal>

      <Modal
        isOpen={resetModal} onClose={() => setResetModal(false)}
        title="Полный сброс прогресса?"
        footer={<><BtnSecondary onClick={() => setResetModal(false)}>Отмена</BtnSecondary><button onClick={doReset} disabled={saving} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-60">Сбросить</button></>}
      >
        <p className="text-sm text-gray-600">Все логи будут удалены. Старт = сегодня, день 1. Анкета и уровень сохраняются.</p>
      </Modal>

      <Modal
        isOpen={onboardingModal} onClose={() => setOnboardingModal(false)}
        title="Сбросить онбординг?"
        footer={<><BtnSecondary onClick={() => setOnboardingModal(false)}>Отмена</BtnSecondary><button onClick={doResetOnboarding} disabled={saving} className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 transition-colors disabled:opacity-60">Сбросить всё</button></>}
      >
        <p className="text-sm text-gray-600">Все логи и анкета будут удалены. Уровень и дата старта очищаются. Пользователь снова пройдёт онбординг с нуля.</p>
      </Modal>
    </div>
  )
}

// ─── Checkins Tab ─────────────────────────────────────────────────────────────
function CheckinsTab({ logs }) {
  const [open, setOpen] = useState(null)

  return (
    <div className="flex flex-col gap-2">
      {logs.length === 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-10 text-center text-gray-400 text-sm">
          Нет данных
        </div>
      )}
      {logs.map(log => {
        const isOpen = open === log.id
        const day    = log.calendar_day ?? log.day_index ?? '?'

        return (
          <div key={log.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <button
              className="w-full flex items-center gap-4 px-5 py-3.5 hover:bg-gray-50 transition-colors text-left"
              onClick={() => setOpen(isOpen ? null : log.id)}
            >
              <span className="text-sm font-medium text-gray-700 w-16 shrink-0">День {day}</span>
              <span className="text-sm text-gray-500 w-28 shrink-0">{formatDate(log.date)}</span>
              <span className="text-sm text-gray-700 flex-1">{log.workout ? DAY_TYPE[log.workout.day_type] : '—'}</span>
              {log.assigned_version && <Badge value={log.assigned_version} label={VERSION_LABELS[log.assigned_version]} />}
              {log.completion_status && <Badge value={log.completion_status} label={COMPLETION[log.completion_status]} />}
              {log.red_flag && <Flag size={13} className="text-red-500" />}
              <span className="text-gray-400 ml-1 shrink-0">
                {isOpen ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
              </span>
            </button>

            {isOpen && (
              <div className="border-t border-gray-100 px-5 py-4 grid grid-cols-2 gap-8">
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Утренний чек-ин</p>
                  <InfoRow label="Самочувствие" value={WELLBEING[log.wellbeing]} />
                  <InfoRow label="Сон" value={SLEEP[log.sleep_quality]} />
                  <InfoRow label="Боль" value={PAIN[log.pain_level]} />
                  <InfoRow label="Усиливается" value={log.pain_increases == null ? null : log.pain_increases ? 'Да' : 'Нет'} />
                  <InfoRow label="Стресс" value={STRESS[log.stress_level]} />
                  <InfoRow label="Red flag" value={log.red_flag ? '🚩 Да' : null} />
                  <InfoRow label="Накопл. усталость" value={log.fatigue_reduction ? '⚠️ Да' : null} />
                </div>
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Тренировка и вечер</p>
                  <InfoRow label="Назначена версия" value={VERSION_LABELS[log.assigned_version]} />
                  <InfoRow label="Workout ID" value={log.assigned_workout_id ? `#${log.assigned_workout_id}` : null} />
                  <div className="border-b border-gray-200 my-2" />
                  <InfoRow label="Статус" value={COMPLETION[log.completion_status]} />
                  <InfoRow label="Усилие" value={log.effort_level ? `${log.effort_level} / 5` : null} />
                  <InfoRow label="Боль во время" value={log.completion_pain == null ? null : log.completion_pain ? 'Да' : 'Нет'} />
                  <InfoRow label="Чекин выполнен" value={log.checkin_done ? 'Да' : 'Нет'} />
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function UserDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const toast = useToast()

  const [user, setUser]     = useState(null)
  const [logs, setLogs]     = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab]       = useState('profile')

  const [levelModal, setLevelModal]   = useState(false)
  const [startModal, setStartModal]   = useState(false)
  const [pauseModal, setPauseModal]   = useState(false)
  const [newLevel, setNewLevel]       = useState(1)
  const [newStartDate, setNewStartDate] = useState('')
  const [saving, setSaving]           = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [uRes, lRes] = await Promise.all([
        api.get(`/users/${id}`),
        api.get(`/users/${id}/logs`),
      ])
      setUser(uRes.data)
      setLogs(lRes.data)
      setNewLevel(uRes.data.level || 1)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [id])

  useEffect(() => { load() }, [load])

  async function saveLevel() {
    setSaving(true)
    try {
      await api.put(`/users/${id}/level`, { level: newLevel })
      toast('Уровень обновлён')
      setLevelModal(false)
      load()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  async function saveStartDate() {
    setSaving(true)
    try {
      await api.put(`/users/${id}/start-date`, { start_date: newStartDate })
      toast('Дата старта обновлена')
      setStartModal(false)
      load()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  async function savePause() {
    setSaving(true)
    const newStatus = user.status === 'active' ? 'paused' : 'active'
    try {
      await api.put(`/users/${id}/status`, { status: newStatus })
      toast(newStatus === 'paused' ? 'Программа приостановлена' : 'Программа возобновлена')
      setPauseModal(false)
      load()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return <div className="text-center py-12 text-gray-400">Пользователь не найден</div>
  }

  const displayName = user.full_name
    || [user.last_name, user.first_name].filter(Boolean).join(' ')
    || `ID ${user.telegram_id}`
  const initials = displayName.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()

  return (
    <div>
      <button
        onClick={() => navigate('/users')}
        className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-5 transition-colors"
      >
        <ArrowLeft size={15} /> Назад к списку
      </button>

      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-5 mb-6">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center text-base font-semibold">
            {initials}
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">{displayName}</h1>
            <div className="flex items-center gap-2 mt-1.5">
              {user.level && <Badge value="default" label={LEVELS[user.level]} />}
              {user.status && <Badge value={user.status} label={STATUS_LABELS[user.status]} />}
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <BtnSecondary onClick={() => setLevelModal(true)}>Изменить уровень</BtnSecondary>
          <BtnSecondary onClick={() => setStartModal(true)}>Назначить старт</BtnSecondary>
          <button
            onClick={() => setPauseModal(true)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              user.status === 'active'
                ? 'bg-yellow-100 text-yellow-700 hover:bg-yellow-200'
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            }`}
          >
            {user.status === 'active' ? 'Пауза' : 'Возобновить'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-0 mb-6 border-b border-gray-200">
        {[['profile','Профиль'],['progress','Прогресс'],['checkins','Чекины'],['testing','🧪 Тест']].map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? 'border-violet-600 text-violet-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'profile'   && <ProfileTab user={user} />}
      {tab === 'progress'  && <ProgressTab logs={logs} onReload={load} />}
      {tab === 'checkins'  && <CheckinsTab logs={logs} />}
      {tab === 'testing'   && <TestingTab userId={id} onReload={load} />}

      {/* Level modal */}
      <Modal
        isOpen={levelModal}
        onClose={() => setLevelModal(false)}
        title={`Изменить уровень — ${displayName}`}
        footer={<><BtnSecondary onClick={() => setLevelModal(false)}>Отмена</BtnSecondary><BtnPrimary onClick={saveLevel} disabled={saving}>Сохранить</BtnPrimary></>}
      >
        <div className="flex flex-col gap-2">
          {Object.entries(LEVELS).map(([k, v]) => (
            <label key={k} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${newLevel === +k ? 'border-violet-300 bg-violet-50' : 'border-gray-200 hover:bg-gray-50'}`}>
              <input type="radio" name="lvl" value={k} checked={newLevel === +k} onChange={() => setNewLevel(+k)} className="accent-violet-600" />
              <span className="text-sm font-medium">{k} — {v}</span>
              {user.level === +k && <span className="ml-auto text-xs text-violet-500 font-medium">Текущий</span>}
            </label>
          ))}
        </div>
      </Modal>

      {/* Start date modal */}
      <Modal
        isOpen={startModal}
        onClose={() => setStartModal(false)}
        title={`Дата старта — ${displayName}`}
        footer={<><BtnSecondary onClick={() => setStartModal(false)}>Отмена</BtnSecondary><BtnPrimary onClick={saveStartDate} disabled={saving || !newStartDate}>Сохранить</BtnPrimary></>}
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Дата старта программы</label>
          <input
            type="date"
            value={newStartDate}
            onChange={e => setNewStartDate(e.target.value)}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
          />
        </div>
      </Modal>

      {/* Pause modal */}
      <Modal
        isOpen={pauseModal}
        onClose={() => setPauseModal(false)}
        title={user.status === 'active' ? 'Поставить на паузу?' : 'Возобновить программу?'}
        footer={<><BtnSecondary onClick={() => setPauseModal(false)}>Отмена</BtnSecondary><BtnPrimary onClick={savePause} disabled={saving}>Подтвердить</BtnPrimary></>}
      >
        <p className="text-sm text-gray-600">
          {user.status === 'active'
            ? `Программа пользователя ${displayName} будет приостановлена.`
            : `Программа пользователя ${displayName} будет возобновлена.`
          }
        </p>
      </Modal>
    </div>
  )
}
