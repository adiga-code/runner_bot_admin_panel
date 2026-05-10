import { useState, useEffect, useCallback } from 'react'
import { Plus, Pencil, Trash2 } from 'lucide-react'
import api from '../api/axios'
import Modal from '../components/Modal'
import { useToast } from '../components/Toast'

const LEVELS  = { 1: 'L1 Start', 2: 'L2 Return', 3: 'L3 Base' }
const FORMATS = { gym: '🏋️ Зал', home: '🏠 Дома' }
const PERIODS = {
  '':                'Универсальный (любой период)',
  base_in:           'Base-In',
  base:              'Base',
  preparatory:       'Preparatory',
  recovery_period:   'Recovery period',
}
const VERSIONS = { base: 'Base (полная)', light: 'Light (−20%)' }

const EMPTY = {
  level: '1', version: 'base', strength_format: 'gym',
  period: '', title: '', text: '', micro_learning: '', video_url: '',
}

function Badge({ label, color }) {
  const colors = {
    green:  'bg-green-100 text-green-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    gray:   'bg-gray-100 text-gray-500',
    violet: 'bg-violet-100 text-violet-700',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[color] || colors.gray}`}>
      {label}
    </span>
  )
}

export default function WorkoutTemplates() {
  const toast = useToast()
  const [templates, setTemplates] = useState([])
  const [loading, setLoading]     = useState(true)
  const [filterLevel,   setFilterLevel]   = useState('')
  const [filterFormat,  setFilterFormat]  = useState('')
  const [filterVersion, setFilterVersion] = useState('')
  const [modal, setModal]         = useState(null)   // null | 'new' | template-object
  const [form, setForm]           = useState(EMPTY)
  const [deleteTarget, setDelete] = useState(null)
  const [saving, setSaving]       = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = { day_type: 'strength' }
      if (filterLevel)   params.level            = filterLevel
      if (filterFormat)  params.strength_format  = filterFormat
      if (filterVersion) params.version          = filterVersion
      const { data } = await api.get('/workout-templates', { params })
      setTemplates(data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [filterLevel, filterFormat, filterVersion])

  useEffect(() => { load() }, [load])

  function setF(k, v) { setForm(f => ({ ...f, [k]: v })) }

  function openCreate() { setForm(EMPTY); setModal('new') }
  function openEdit(t) {
    setForm({
      level:           String(t.level),
      version:         t.version || 'base',
      strength_format: t.strength_format || 'gym',
      period:          t.period || '',
      title:           t.title || '',
      text:            t.text || '',
      micro_learning:  t.micro_learning || '',
      video_url:       t.video_url || '',
    })
    setModal(t)
  }

  async function save() {
    if (!form.title.trim()) { toast('Укажи название', 'error'); return }
    if (!form.text.trim())  { toast('Заполни текст тренировки', 'error'); return }
    setSaving(true)
    try {
      const payload = {
        day_type:        'strength',
        level:           parseInt(form.level),
        version:         form.version,
        strength_format: form.strength_format || null,
        period:          form.period || null,
        title:           form.title.trim(),
        text:            form.text.trim(),
        micro_learning:  form.micro_learning.trim() || null,
        video_url:       form.video_url.trim() || null,
        run_subtype:     null,
        intensity_kind:  null,
      }
      if (modal === 'new') {
        await api.post('/workout-templates', payload)
        toast('Шаблон создан')
      } else {
        await api.put(`/workout-templates/${modal.id}`, payload)
        toast('Сохранено')
      }
      setModal(null)
      load()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  async function doDelete() {
    setSaving(true)
    try {
      await api.delete(`/workout-templates/${deleteTarget.id}`)
      toast('Удалено')
      setDelete(null)
      load()
    } catch { toast('Ошибка удаления', 'error') }
    setSaving(false)
  }

  const cls = "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
  const selCls = "border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-violet-500"

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">💪 Силовые тренировки</h1>
          <p className="text-sm text-gray-400 mt-0.5">Шаблоны для L1–L3. Беговые тренировки генерируются автоматически.</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors"
        >
          <Plus size={15} /> Добавить шаблон
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <select value={filterLevel} onChange={e => setFilterLevel(e.target.value)} className={selCls}>
          <option value="">Все уровни</option>
          {Object.entries(LEVELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filterFormat} onChange={e => setFilterFormat(e.target.value)} className={selCls}>
          <option value="">Зал и дома</option>
          {Object.entries(FORMATS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filterVersion} onChange={e => setFilterVersion(e.target.value)} className={selCls}>
          <option value="">Base и Light</option>
          <option value="base">Base</option>
          <option value="light">Light</option>
        </select>
        <span className="text-sm text-gray-400 self-center ml-1">{templates.length} шаблонов</span>
      </div>

      {/* Cards grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : templates.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <p className="text-base mb-1">Шаблонов не найдено</p>
          <p className="text-sm">Создайте первый или измените фильтры</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {templates.map(t => (
            <div key={t.id} className="bg-white border border-gray-200 rounded-xl p-5 flex gap-4 hover:border-violet-200 transition-colors">
              {/* Meta */}
              <div className="flex flex-col gap-1.5 w-48 shrink-0">
                <div className="flex gap-1.5 flex-wrap">
                  <Badge label={LEVELS[t.level] || `L${t.level}`} color="violet" />
                  <Badge label={t.version === 'base' ? 'Base' : 'Light'} color={t.version === 'base' ? 'green' : 'yellow'} />
                </div>
                <div className="flex gap-1.5 flex-wrap">
                  {t.strength_format && <Badge label={FORMATS[t.strength_format] || t.strength_format} color="gray" />}
                  {t.period && <Badge label={t.period} color="gray" />}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 text-sm mb-1">{t.title}</p>
                <p className="text-xs text-gray-400 line-clamp-2 whitespace-pre-line">{t.text}</p>
                {t.micro_learning && (
                  <p className="text-xs text-blue-500 mt-1.5 line-clamp-1">💡 {t.micro_learning}</p>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-1 shrink-0 self-start">
                <button
                  onClick={() => openEdit(t)}
                  className="p-2 rounded-lg hover:bg-violet-50 text-gray-400 hover:text-violet-600 transition-colors"
                >
                  <Pencil size={14} />
                </button>
                <button
                  onClick={() => setDelete(t)}
                  className="p-2 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit modal */}
      {modal !== null && (
        <Modal
          isOpen
          onClose={() => setModal(null)}
          title={modal === 'new' ? 'Новый шаблон силовой тренировки' : `Редактировать: ${modal.title}`}
          footer={
            <div className="flex gap-2 justify-end w-full">
              <button onClick={() => setModal(null)} className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                Отмена
              </button>
              <button onClick={save} disabled={saving} className="px-4 py-2 text-sm bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-60">
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
            </div>
          }
        >
          <div className="space-y-4">
            {/* Row 1: Level + Format */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Уровень</label>
                <select value={form.level} onChange={e => setF('level', e.target.value)} className={cls}>
                  {Object.entries(LEVELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Формат</label>
                <select value={form.strength_format} onChange={e => setF('strength_format', e.target.value)} className={cls}>
                  <option value="">Любой формат</option>
                  {Object.entries(FORMATS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
            </div>

            {/* Row 2: Version + Period */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Версия</label>
                <select value={form.version} onChange={e => setF('version', e.target.value)} className={cls}>
                  {Object.entries(VERSIONS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <p className="text-xs text-gray-400 mt-1">Light — объём −20% от Base</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Период</label>
                <select value={form.period} onChange={e => setF('period', e.target.value)} className={cls}>
                  {Object.entries(PERIODS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <p className="text-xs text-gray-400 mt-1">Универсальный — подходит для любого периода</p>
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Название <span className="text-red-400">*</span>
              </label>
              <input
                value={form.title}
                onChange={e => setF('title', e.target.value)}
                className={cls}
                placeholder="Силовая тренировка — зал, Base"
              />
            </div>

            {/* Text */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Текст тренировки <span className="text-red-400">*</span>
              </label>
              <p className="text-xs text-gray-400 mb-1.5">
                Пиши конкретно: упражнения, подходы, повторения. Можно использовать <code className="bg-gray-100 px-1 rounded">{'{minutes}'}</code> для общего времени.
              </p>
              <textarea
                value={form.text}
                onChange={e => setF('text', e.target.value)}
                rows={10}
                className={cls + ' resize-y'}
                placeholder={
                  '💪 Разминка: 5 мин динамическая растяжка\n\n' +
                  'Основная часть:\n' +
                  '• Приседания со штангой — 4×8 (RPE 7-8)\n' +
                  '• Жим лёжа — 4×8 (RPE 7-8)\n' +
                  '• Тяга в наклоне — 3×10 (RPE 6-7)\n' +
                  '• Выпады с гантелями — 3×12 каждая нога\n\n' +
                  '🧘 Заминка: 5 мин растяжка'
                }
              />
            </div>

            {/* Micro-learning */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Микро-обучение</label>
              <textarea
                value={form.micro_learning}
                onChange={e => setF('micro_learning', e.target.value)}
                rows={2}
                className={cls + ' resize-none'}
                placeholder="Силовые тренировки повышают экономичность бега и снижают риск травм..."
              />
            </div>

            {/* Video URL */}
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Ссылка на видео</label>
              <input
                value={form.video_url}
                onChange={e => setF('video_url', e.target.value)}
                className={cls}
                placeholder="https://youtube.com/..."
              />
            </div>
          </div>
        </Modal>
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <Modal
          isOpen
          onClose={() => setDelete(null)}
          title="Удалить шаблон?"
          footer={
            <>
              <button onClick={() => setDelete(null)} className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">
                Отмена
              </button>
              <button onClick={doDelete} disabled={saving} className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-60">
                Удалить
              </button>
            </>
          }
        >
          <p className="text-sm text-gray-700 font-medium">{deleteTarget.title}</p>
          <p className="text-xs text-gray-400 mt-1">
            {LEVELS[deleteTarget.level]} · {FORMATS[deleteTarget.strength_format] || '—'} · {deleteTarget.version}
          </p>
          <p className="text-xs text-gray-400 mt-3">Это действие необратимо.</p>
        </Modal>
      )}
    </div>
  )
}
