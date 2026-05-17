import { useState, useEffect, useCallback, useRef } from 'react'
import { Plus, Pencil, Trash2, RefreshCw, ToggleLeft, ToggleRight, Upload } from 'lucide-react'
import api from '../api/axios'
import Modal from '../components/Modal'
import { useToast } from '../components/Toast'

const CATEGORIES = [
  { value: 'free', label: '📖 База (бесплатно)' },
  { value: 'premium', label: '⭐ Премиум (платно)' },
]

function UploadModal({ onClose, onSaved }) {
  const toast = useToast()
  const fileRef = useRef(null)
  const [form, setForm] = useState({
    title: '',
    description: '',
    category: 'free',
    price_rub: '',
    sort_order: 0,
  })
  const [file, setFile] = useState(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!file) { toast('Выберите файл', 'error'); return }
    if (!form.title.trim()) { toast('Укажите название', 'error'); return }
    if (form.category === 'premium' && !form.price_rub) {
      toast('Укажите цену для премиум-материала', 'error'); return
    }

    setSaving(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', form.title.trim())
      fd.append('description', form.description.trim())
      fd.append('category', form.category)
      if (form.price_rub) fd.append('price_rub', Number(form.price_rub))
      fd.append('sort_order', Number(form.sort_order))

      await api.post('/materials/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      toast('✅ Материал загружен')
      onSaved()
      onClose()
    } catch (e) {
      toast(e?.response?.data?.detail || 'Ошибка загрузки', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal isOpen onClose={onClose} title="Загрузить материал">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* File picker */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Файл *</label>
          <div
            onClick={() => fileRef.current?.click()}
            className="border-2 border-dashed border-gray-200 rounded-xl p-6 text-center cursor-pointer hover:border-violet-300 hover:bg-violet-50 transition-colors"
          >
            <Upload size={20} className="mx-auto text-gray-400 mb-2" />
            {file ? (
              <p className="text-sm text-violet-700 font-medium">{file.name}</p>
            ) : (
              <p className="text-sm text-gray-400">Нажмите для выбора PDF или изображения</p>
            )}
          </div>
          <input ref={fileRef} type="file" accept=".pdf,image/*" className="hidden" onChange={e => setFile(e.target.files[0])} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Название *</label>
          <input
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="Название материала"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Описание</label>
          <textarea
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            rows={3}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 resize-none"
            placeholder="Краткое описание"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Раздел *</label>
          <select
            value={form.category}
            onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
          >
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>

        {form.category === 'premium' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Цена (₽) *</label>
            <input
              type="number"
              min={1}
              value={form.price_rub}
              onChange={e => setForm(f => ({ ...f, price_rub: e.target.value }))}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
              placeholder="например 590"
            />
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Порядок сортировки</label>
          <input
            type="number"
            value={form.sort_order}
            onChange={e => setForm(f => ({ ...f, sort_order: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>

        <div className="flex gap-3 pt-1">
          <button type="button" onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50">
            Отмена
          </button>
          <button
            type="submit"
            disabled={saving}
            className="flex-1 bg-violet-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-violet-700 disabled:opacity-60"
          >
            {saving ? 'Загружаем...' : 'Загрузить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function EditModal({ material, onClose, onSaved }) {
  const toast = useToast()
  const [form, setForm] = useState({
    title: material.title || '',
    description: material.description || '',
    category: material.category || 'free',
    price_rub: material.price_rub || '',
    sort_order: material.sort_order ?? 0,
  })
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setSaving(true)
    try {
      await api.put(`/materials/${material.id}`, {
        title: form.title.trim(),
        description: form.description.trim() || null,
        category: form.category,
        price_rub: form.price_rub ? Number(form.price_rub) : null,
        sort_order: Number(form.sort_order),
      })
      toast('✅ Сохранено')
      onSaved()
      onClose()
    } catch (e) {
      toast(e?.response?.data?.detail || 'Ошибка', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal isOpen onClose={onClose} title="Редактировать материал">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Название *</label>
          <input
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Описание</label>
          <textarea
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            rows={3}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400 resize-none"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Раздел</label>
          <select
            value={form.category}
            onChange={e => setForm(f => ({ ...f, category: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
          >
            {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Цена (₽) — для премиум</label>
          <input
            type="number"
            min={1}
            value={form.price_rub}
            onChange={e => setForm(f => ({ ...f, price_rub: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
            placeholder="пусто = бесплатно"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Порядок сортировки</label>
          <input
            type="number"
            value={form.sort_order}
            onChange={e => setForm(f => ({ ...f, sort_order: e.target.value }))}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-400"
          />
        </div>
        <div className="flex gap-3 pt-1">
          <button type="button" onClick={onClose} className="flex-1 border border-gray-200 rounded-lg py-2.5 text-sm font-medium text-gray-600 hover:bg-gray-50">
            Отмена
          </button>
          <button type="submit" disabled={saving} className="flex-1 bg-violet-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-violet-700 disabled:opacity-60">
            {saving ? 'Сохраняем...' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

export default function Materials() {
  const toast = useToast()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const [showUpload, setShowUpload] = useState(false)
  const [editing, setEditing] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = {}
      if (filter !== 'all') params.category = filter
      const res = await api.get('/materials', { params })
      setItems(Array.isArray(res.data) ? res.data : [])
    } catch {
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => { load() }, [load])

  async function toggleActive(m) {
    try {
      await api.put(`/materials/${m.id}`, { is_active: !m.is_active })
      setItems(prev => prev.map(i => i.id === m.id ? { ...i, is_active: !i.is_active } : i))
    } catch {
      toast('Ошибка', 'error')
    }
  }

  async function deleteMaterial(m) {
    if (!confirm(`Удалить «${m.title}»?`)) return
    try {
      await api.delete(`/materials/${m.id}`)
      setItems(prev => prev.filter(i => i.id !== m.id))
      toast('Удалено')
    } catch {
      toast('Ошибка удаления', 'error')
    }
  }

  const filtered = filter === 'all' ? items : items.filter(i => i.category === filter)

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Материалы</h1>
          <p className="text-sm text-gray-500 mt-1">Гайды и файлы для пользователей бота</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <RefreshCw size={15} />
          </button>
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 bg-violet-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-violet-700 transition-colors"
          >
            <Plus size={16} />
            Загрузить
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-5">
        {[
          { value: 'all', label: 'Все' },
          { value: 'free', label: '📖 База' },
          { value: 'premium', label: '⭐ Премиум' },
        ].map(tab => (
          <button
            key={tab.value}
            onClick={() => setFilter(tab.value)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
              filter === tab.value
                ? 'bg-violet-600 text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-24">
          <div className="w-6 h-6 border-2 border-violet-600 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-12 text-center">
          <div className="text-4xl mb-3">📭</div>
          <p className="text-gray-500 text-sm">Материалов нет. Нажмите «Загрузить», чтобы добавить первый.</p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Название</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Раздел</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Цена</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Тип</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Порядок</th>
                <th className="text-center px-4 py-3 text-xs font-medium text-gray-500 uppercase">Активен</th>
                <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Действия</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((m, i) => (
                <tr key={m.id} className={`border-b border-gray-100 hover:bg-gray-50 ${!m.is_active ? 'opacity-50' : ''}`}>
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{m.title}</div>
                    {m.description && (
                      <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">{m.description}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      m.category === 'premium'
                        ? 'bg-amber-50 text-amber-700'
                        : 'bg-green-50 text-green-700'
                    }`}>
                      {m.category === 'premium' ? '⭐ Премиум' : '📖 База'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700">
                    {m.price_rub ? `${m.price_rub} ₽` : <span className="text-gray-400">бесплатно</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-500 uppercase text-xs">{m.file_type || '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{m.sort_order}</td>
                  <td className="px-4 py-3 text-center">
                    <button onClick={() => toggleActive(m)} className="text-gray-400 hover:text-violet-600 transition-colors">
                      {m.is_active
                        ? <ToggleRight size={20} className="text-violet-600" />
                        : <ToggleLeft size={20} />
                      }
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2 justify-end">
                      <button
                        onClick={() => setEditing(m)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-violet-600 hover:bg-violet-50 transition-colors"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => deleteMaterial(m)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showUpload && <UploadModal onClose={() => setShowUpload(false)} onSaved={load} />}
      {editing && <EditModal material={editing} onClose={() => setEditing(null)} onSaved={load} />}
    </div>
  )
}
