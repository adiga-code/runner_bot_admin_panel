import { useState, useEffect, useCallback } from 'react'
import { Plus, Pencil, Trash2, Eye, EyeOff } from 'lucide-react'
import api from '../api/axios'
import Modal from '../components/Modal'
import { useToast } from '../components/Toast'

const LEVELS       = { 1:'Start', 2:'Return', 3:'Base', 4:'Stability', 5:'Performance' }
const DAY_TYPES    = { run:'🏃 Бег', strength:'💪 Силовая', recovery:'🚶 Восстановление', rest:'😴 Отдых' }
const VERSIONS     = { base:'Base', light:'Light', recovery:'Recovery' }
const RUN_SUBTYPES = { long:'Длинный', aerobic:'Аэробный', easy:'Лёгкий', recovery_run:'Восстановительный', run_walk:'Бег/шаг', tempo:'Темп', intervals:'Интервалы' }
const PERIODS      = { base_in:'base_in', base:'base', preparatory:'preparatory', recovery_period:'recovery_period' }
const FORMATS      = { gym:'🏋️ Зал', home:'🏠 Дома' }

const VERSION_COLORS = { base:'bg-green-100 text-green-700', light:'bg-yellow-100 text-yellow-700', recovery:'bg-blue-100 text-blue-700' }

const EMPTY_FORM = {
  level: '1', day_type: 'run', run_subtype: '', version: 'base',
  intensity_kind: '', period: '', strength_format: '',
  title: '', short_title: '', text: '', micro_learning: '', video_url: '',
}

export default function WorkoutTemplates() {
  const toast = useToast()
  const [templates, setTemplates] = useState([])
  const [loading, setLoading]     = useState(true)
  const [filters, setFilters]     = useState({ level:'', day_type:'', run_subtype:'', version:'', period:'' })
  const [editModal, setEditModal] = useState(null)   // null = closed, 'new' = create, obj = edit
  const [form, setForm]           = useState(EMPTY_FORM)
  const [preview, setPreview]     = useState(false)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [saving, setSaving]       = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.level)      params.level      = filters.level
      if (filters.day_type)   params.day_type   = filters.day_type
      if (filters.run_subtype) params.run_subtype = filters.run_subtype
      if (filters.version)    params.version    = filters.version
      if (filters.period)     params.period     = filters.period
      const { data } = await api.get('/workout-templates', { params })
      setTemplates(data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  function setF(k, v) { setFilters(f => ({ ...f, [k]: v })) }
  function setFrm(k, v) { setForm(f => ({ ...f, [k]: v })) }

  function openCreate() {
    setForm(EMPTY_FORM)
    setPreview(false)
    setEditModal('new')
  }

  function openEdit(t) {
    setForm({
      level:          String(t.level),
      day_type:       t.day_type || 'run',
      run_subtype:    t.run_subtype || '',
      version:        t.version || 'base',
      intensity_kind: t.intensity_kind || '',
      period:         t.period || '',
      strength_format: t.strength_format || '',
      title:          t.title || '',
      short_title:    t.short_title || '',
      text:           t.text || '',
      micro_learning: t.micro_learning || '',
      video_url:      t.video_url || '',
    })
    setPreview(false)
    setEditModal(t)
  }

  async function save() {
    if (!form.title.trim() || !form.text.trim()) {
      toast('Заполни название и текст', 'error'); return
    }
    setSaving(true)
    try {
      const payload = {
        ...form,
        level:          parseInt(form.level),
        run_subtype:    form.run_subtype || null,
        intensity_kind: form.intensity_kind || null,
        period:         form.period || null,
        strength_format: form.strength_format || null,
        short_title:    form.short_title || null,
        micro_learning: form.micro_learning || null,
        video_url:      form.video_url || null,
      }
      if (editModal === 'new') {
        await api.post('/workout-templates', payload)
        toast('Шаблон создан')
      } else {
        await api.put(`/workout-templates/${editModal.id}`, payload)
        toast('Шаблон сохранён')
      }
      setEditModal(null)
      load()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  async function doDelete() {
    setSaving(true)
    try {
      await api.delete(`/workout-templates/${deleteTarget.id}`)
      toast('Удалено')
      setDeleteTarget(null)
      load()
    } catch { toast('Ошибка удаления', 'error') }
    setSaving(false)
  }

  // Rendered preview with placeholder substitution
  function renderPreview(text) {
    const minutes = 60, warmup = 12, cooldown = 9, main = 39
    return text
      .replace(/\{minutes\}/g, minutes)
      .replace(/\{warmup_minutes\}/g, warmup)
      .replace(/\{main_minutes\}/g, main)
      .replace(/\{cooldown_minutes\}/g, cooldown)
      .replace(/\{total_minutes\}/g, minutes)
  }

  const selectCls = "border border-gray-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-violet-500"
  const inputCls  = "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"

  return (
    <div>
      <div className="flex items-center justify-between border-b border-gray-200 pb-4 mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Шаблоны тренировок</h1>
          <p className="text-sm text-gray-500 mt-0.5">Новая система (L1–L3). Не привязаны к дню 1-28.</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors"
        >
          <Plus size={16} /> Добавить шаблон
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-5">
        <select value={filters.level} onChange={e => setF('level', e.target.value)} className={selectCls}>
          <option value="">Все уровни</option>
          {Object.entries(LEVELS).map(([k,v]) => <option key={k} value={k}>L{k} {v}</option>)}
        </select>
        <select value={filters.day_type} onChange={e => setF('day_type', e.target.value)} className={selectCls}>
          <option value="">Все типы</option>
          {Object.entries(DAY_TYPES).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.run_subtype} onChange={e => setF('run_subtype', e.target.value)} className={selectCls}>
          <option value="">Все подтипы</option>
          {Object.entries(RUN_SUBTYPES).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.version} onChange={e => setF('version', e.target.value)} className={selectCls}>
          <option value="">Все версии</option>
          {Object.entries(VERSIONS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.period} onChange={e => setF('period', e.target.value)} className={selectCls}>
          <option value="">Все периоды</option>
          <option value="__null__">Универсальный (без периода)</option>
          {Object.entries(PERIODS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <span className="text-sm text-gray-400 self-center">{templates.length} шаблонов</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg mb-1">Шаблонов не найдено</p>
            <p className="text-sm">Добавьте первый шаблон или измените фильтры</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100">
                {['Уровень','Тип','Подтип','Версия','Период','Формат','Название','Текст',''].map(h => (
                  <th key={h} className="px-4 py-3 text-left text-xs text-gray-400 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {templates.map(t => (
                <tr key={t.id} className="border-b border-gray-50 last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-2.5 text-gray-500 whitespace-nowrap">L{t.level} <span className="text-gray-400">{LEVELS[t.level]}</span></td>
                  <td className="px-4 py-2.5 text-gray-700 whitespace-nowrap">{DAY_TYPES[t.day_type] || t.day_type}</td>
                  <td className="px-4 py-2.5 text-gray-500 whitespace-nowrap">{RUN_SUBTYPES[t.run_subtype] || t.run_subtype || '—'}</td>
                  <td className="px-4 py-2.5">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${VERSION_COLORS[t.version] || 'bg-gray-100 text-gray-600'}`}>
                      {t.version}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-gray-400 text-xs whitespace-nowrap">{t.period || '—'}</td>
                  <td className="px-4 py-2.5 text-gray-400 text-xs whitespace-nowrap">{FORMATS[t.strength_format] || t.strength_format || '—'}</td>
                  <td className="px-4 py-2.5 font-medium text-gray-800 max-w-[180px] truncate">{t.title}</td>
                  <td className="px-4 py-2.5 text-gray-400 max-w-[240px] truncate">{t.text}</td>
                  <td className="px-4 py-2.5 whitespace-nowrap">
                    <div className="flex gap-1">
                      <button onClick={() => openEdit(t)} className="p-1.5 rounded hover:bg-violet-50 text-gray-400 hover:text-violet-600 transition-colors"><Pencil size={14} /></button>
                      <button onClick={() => setDeleteTarget(t)} className="p-1.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"><Trash2 size={14} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Edit / Create modal */}
      {editModal !== null && (
        <Modal
          isOpen
          onClose={() => setEditModal(null)}
          title={editModal === 'new' ? 'Новый шаблон' : `Редактировать #${editModal.id}`}
          footer={
            <div className="flex items-center justify-between w-full">
              <button
                onClick={() => setPreview(p => !p)}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
              >
                {preview ? <EyeOff size={14} /> : <Eye size={14} />}
                {preview ? 'Редактор' : 'Превью'}
              </button>
              <div className="flex gap-2">
                <button onClick={() => setEditModal(null)} className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Отмена</button>
                <button onClick={save} disabled={saving} className="px-4 py-2 text-sm bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-60">Сохранить</button>
              </div>
            </div>
          }
        >
          {preview ? (
            <div className="space-y-3">
              <p className="text-xs text-gray-400">Превью с подстановкой (60 мин): {renderPreview('{minutes}')} мин</p>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="font-semibold text-gray-900 mb-2">{form.title}</p>
                <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">{renderPreview(form.text)}</pre>
              </div>
              {form.micro_learning && (
                <div className="bg-blue-50 rounded-lg p-3">
                  <p className="text-xs text-blue-500 font-medium mb-1">Микро-обучение</p>
                  <p className="text-sm text-blue-800">{form.micro_learning}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Row 1: level + day_type + version */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Уровень</label>
                  <select value={form.level} onChange={e => setFrm('level', e.target.value)} className={inputCls}>
                    {Object.entries(LEVELS).map(([k,v]) => <option key={k} value={k}>L{k} {v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Тип</label>
                  <select value={form.day_type} onChange={e => setFrm('day_type', e.target.value)} className={inputCls}>
                    {Object.entries(DAY_TYPES).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Версия</label>
                  <select value={form.version} onChange={e => setFrm('version', e.target.value)} className={inputCls}>
                    {Object.entries(VERSIONS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>

              {/* Row 2: run_subtype + period + strength_format */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Подтип бега</label>
                  <select value={form.run_subtype} onChange={e => setFrm('run_subtype', e.target.value)} className={inputCls}>
                    <option value="">— нет —</option>
                    {Object.entries(RUN_SUBTYPES).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Период</label>
                  <select value={form.period} onChange={e => setFrm('period', e.target.value)} className={inputCls}>
                    <option value="">Универсальный</option>
                    {Object.entries(PERIODS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Формат силовой</label>
                  <select value={form.strength_format} onChange={e => setFrm('strength_format', e.target.value)} className={inputCls}>
                    <option value="">— нет —</option>
                    {Object.entries(FORMATS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
              </div>

              {/* Title */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Название <span className="text-red-400">*</span></label>
                <input value={form.title} onChange={e => setFrm('title', e.target.value)} className={inputCls} placeholder="Аэробный бег" />
              </div>

              {/* Text */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">
                  Текст тренировки <span className="text-red-400">*</span>
                  <span className="ml-2 font-normal text-gray-400">плейсхолдеры: {'{minutes}'} {'{warmup_minutes}'} {'{main_minutes}'} {'{cooldown_minutes}'}</span>
                </label>
                <textarea
                  value={form.text}
                  onChange={e => setFrm('text', e.target.value)}
                  rows={8}
                  className={inputCls + ' resize-y font-mono text-xs'}
                  placeholder="Разминка: {warmup_minutes} мин ходьба&#10;Основная часть: {main_minutes} мин аэробный бег (Z2)&#10;Заминка: {cooldown_minutes} мин ходьба"
                />
              </div>

              {/* Micro learning */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Микро-обучение (необязательно)</label>
                <textarea
                  value={form.micro_learning}
                  onChange={e => setFrm('micro_learning', e.target.value)}
                  rows={3}
                  className={inputCls + ' resize-y text-xs'}
                  placeholder="Аэробный бег укрепляет сердце и развивает базовую выносливость..."
                />
              </div>

              {/* Video URL */}
              <div>
                <label className="block text-xs text-gray-500 mb-1">Ссылка на видео (необязательно)</label>
                <input value={form.video_url} onChange={e => setFrm('video_url', e.target.value)} className={inputCls} placeholder="https://..." />
              </div>
            </div>
          )}
        </Modal>
      )}

      {/* Delete confirm */}
      {deleteTarget && (
        <Modal
          isOpen
          onClose={() => setDeleteTarget(null)}
          title="Удалить шаблон?"
          footer={
            <>
              <button onClick={() => setDeleteTarget(null)} className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50">Отмена</button>
              <button onClick={doDelete} disabled={saving} className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-60">Удалить</button>
            </>
          }
        >
          <p className="text-sm text-gray-600">
            <span className="font-medium">{deleteTarget.title}</span> — L{deleteTarget.level} / {deleteTarget.day_type} / {deleteTarget.version}
          </p>
          <p className="text-xs text-gray-400 mt-1">Это действие необратимо.</p>
        </Modal>
      )}
    </div>
  )
}
