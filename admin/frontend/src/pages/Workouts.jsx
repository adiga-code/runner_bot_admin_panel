import { useState, useEffect, useCallback } from 'react'
import { Search, Dumbbell } from 'lucide-react'
import api from '../api/axios'
import Badge from '../components/Badge'
import Modal from '../components/Modal'
import { useToast } from '../components/Toast'

const LEVELS       = { 1:'Start', 2:'Return', 3:'Base', 4:'Stability', 5:'Performance' }
const DAY_TYPES    = { run:'Бег', strength:'Силовая', recovery:'Восстановление', rest:'Отдых' }
const VERSION_LABELS = { base:'Base', light:'Light', recovery:'Recovery' }
const FORMAT_LABELS  = { gym:'🏋️ Зал', home:'🏠 Дома' }

export default function Workouts() {
  const toast = useToast()
  const [workouts, setWorkouts] = useState([])
  const [loading, setLoading]   = useState(true)
  const [filters, setFilters]   = useState({ level:'', day_type:'', version:'', search:'' })
  const [editModal, setEditModal] = useState(null)
  const [form, setForm]         = useState({})
  const [preview, setPreview]   = useState(false)
  const [saving, setSaving]     = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filters.level)    params.level    = filters.level
      if (filters.day_type) params.day_type = filters.day_type
      if (filters.version)  params.version  = filters.version
      if (filters.search)   params.search   = filters.search
      const { data } = await api.get('/workouts', { params })
      setWorkouts(data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [filters])

  useEffect(() => { load() }, [load])

  function openEdit(w) {
    setEditModal(w)
    setForm({
      title:         w.title || '',
      text:          w.text || '',
      micro_learning: w.micro_learning || '',
      video_url:     w.video_url || '',
    })
    setPreview(false)
  }

  async function saveWorkout() {
    setSaving(true)
    try {
      await api.put(`/workouts/${editModal.id}`, form)
      toast('Тренировка сохранена')
      setEditModal(null)
      load()
    } catch { toast('Ошибка сохранения', 'error') }
    setSaving(false)
  }

  function setFilter(key, val) {
    setFilters(f => ({ ...f, [key]: val }))
  }

  return (
    <div>
      <div className="border-b border-gray-200 pb-4 mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Тренировки</h1>
      </div>

      <div className="flex gap-3 mb-4">
        <select value={filters.level} onChange={e => setFilter('level', e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white">
          <option value="">Все уровни</option>
          {Object.entries(LEVELS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.day_type} onChange={e => setFilter('day_type', e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white">
          <option value="">Все типы</option>
          {Object.entries(DAY_TYPES).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select value={filters.version} onChange={e => setFilter('version', e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 bg-white">
          <option value="">Все версии</option>
          {Object.entries(VERSION_LABELS).map(([k,v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={filters.search}
            onChange={e => setFilter('search', e.target.value)}
            placeholder="Поиск по заголовку..."
            className="pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 w-56"
          />
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {['Уровень','День','Тип','Версия','Формат','Заголовок',''].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 6 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-100">
                  {Array.from({ length: 7 }).map((_, j) => (
                    <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-100 rounded animate-pulse w-20" /></td>
                  ))}
                </tr>
              ))
              : workouts.length === 0
                ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-14 text-center">
                      <div className="flex flex-col items-center gap-2 text-gray-400">
                        <Dumbbell size={28} strokeWidth={1.5} />
                        <span className="text-sm">Тренировки не найдены</span>
                      </div>
                    </td>
                  </tr>
                )
                : workouts.map(w => (
                  <tr key={w.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-gray-700">{LEVELS[w.level] || w.level || '—'}</td>
                    <td className="px-4 py-3 text-gray-700">{w.day ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-700">{DAY_TYPES[w.day_type] || w.day_type || '—'}</td>
                    <td className="px-4 py-3">
                      {w.version ? <Badge value={w.version} label={VERSION_LABELS[w.version] || w.version} /> : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-700">{FORMAT_LABELS[w.strength_format] || '—'}</td>
                    <td className="px-4 py-3 text-gray-900 max-w-xs truncate font-medium">{w.title || '—'}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => openEdit(w)}
                        className="bg-white text-gray-700 border border-gray-200 px-3 py-1.5 rounded-lg text-xs hover:bg-gray-50 transition-colors"
                      >
                        Редактировать
                      </button>
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>

      <Modal
        isOpen={!!editModal}
        onClose={() => setEditModal(null)}
        title={editModal
          ? `Тренировка — Уровень ${editModal.level}, День ${editModal.day}${editModal.version ? `, ${VERSION_LABELS[editModal.version] || editModal.version}` : ''}`
          : ''
        }
        footer={
          <>
            <button onClick={() => setEditModal(null)}
              className="bg-white text-gray-700 border border-gray-200 px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
              Отмена
            </button>
            <button onClick={saveWorkout} disabled={saving}
              className="bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 disabled:opacity-60">
              Сохранить
            </button>
          </>
        }
      >
        {editModal && (
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Заголовок</label>
              <input
                value={form.title}
                onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Текст тренировки</label>
              <textarea
                value={form.text}
                onChange={e => setForm(f => ({ ...f, text: e.target.value }))}
                rows={12}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-violet-500 resize-y"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Микро-обучение</label>
              <textarea
                value={form.micro_learning}
                onChange={e => setForm(f => ({ ...f, micro_learning: e.target.value }))}
                rows={4}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 resize-y"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Video URL</label>
              <input
                value={form.video_url}
                onChange={e => setForm(f => ({ ...f, video_url: e.target.value }))}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>
            <div>
              <button
                onClick={() => setPreview(p => !p)}
                className="text-sm text-violet-600 hover:text-violet-700 font-medium"
              >
                {preview ? '▲ Скрыть превью' : '▼ Показать превью'}
              </button>
              {preview && (
                <div className="mt-3 bg-gray-50 rounded-lg p-4 text-sm whitespace-pre-wrap text-gray-700 border border-gray-200 max-h-64 overflow-y-auto">
                  {form.text || <span className="text-gray-400 italic">Нет текста</span>}
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
