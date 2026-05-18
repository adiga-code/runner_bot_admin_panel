import { useState, useEffect, useRef } from 'react'
import { Upload, Trash2, FileText, Image, Video, File } from 'lucide-react'
import api from '../api/axios'
import { useToast } from '../components/Toast'

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`
}

function FileIcon({ filename }) {
  const ext = filename?.split('.').pop()?.toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext)) return <Image size={18} className="text-blue-500" />
  if (['mp4', 'mov', 'webm'].includes(ext)) return <Video size={18} className="text-purple-500" />
  if (ext === 'pdf') return <FileText size={18} className="text-red-500" />
  return <File size={18} className="text-gray-400" />
}

export default function Materials() {
  const toast = useToast()
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef()

  async function loadFiles() {
    try {
      const { data } = await api.get('/materials/list')
      setFiles(data)
    } catch { /* ignore */ }
  }

  useEffect(() => { loadFiles() }, [])

  async function upload(fileList) {
    if (!fileList?.length) return
    setUploading(true)
    let success = 0
    for (const file of Array.from(fileList)) {
      const form = new FormData()
      form.append('file', file)
      try {
        await api.post('/materials/upload', form, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        success++
      } catch (e) {
        const msg = e?.response?.data?.detail || 'Ошибка загрузки'
        toast(`${file.name}: ${msg}`, 'error')
      }
    }
    if (success) toast(`Загружено файлов: ${success}`)
    setUploading(false)
    loadFiles()
  }

  async function deleteFile(filename) {
    try {
      await api.delete(`/materials/${filename}`)
      toast('Файл удалён')
      setFiles(f => f.filter(x => x.filename !== filename))
    } catch { toast('Ошибка удаления', 'error') }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragOver(false)
    upload(e.dataTransfer.files)
  }

  return (
    <div>
      <div className="border-b border-gray-200 pb-4 mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Материалы</h1>
      </div>

      <div
        onDrop={onDrop}
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onClick={() => !uploading && inputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors mb-6 ${
          dragOver ? 'border-violet-400 bg-violet-50' : 'border-gray-200 hover:border-violet-300 hover:bg-gray-50'
        } ${uploading ? 'opacity-60 cursor-not-allowed' : ''}`}
      >
        <Upload size={28} className="mx-auto mb-3 text-gray-400" />
        <p className="text-sm font-medium text-gray-700">
          {uploading ? 'Загрузка...' : 'Перетащите файлы сюда или нажмите для выбора'}
        </p>
        <p className="text-xs text-gray-400 mt-1">Изображения, видео, PDF, DOCX — до 100 МБ</p>
        <input
          ref={inputRef}
          type="file"
          multiple
          className="hidden"
          onChange={e => upload(e.target.files)}
        />
      </div>

      {files.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 w-8"></th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Файл</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Размер</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ссылка</th>
                <th className="px-4 py-3 w-10"></th>
              </tr>
            </thead>
            <tbody>
              {files.map(f => (
                <tr key={f.filename} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3">
                    <FileIcon filename={f.filename} />
                  </td>
                  <td className="px-4 py-3 text-gray-900 font-medium max-w-xs truncate">{f.filename}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{formatSize(f.size)}</td>
                  <td className="px-4 py-3">
                    <a
                      href={f.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-violet-600 hover:text-violet-700 text-xs truncate max-w-xs block"
                      onClick={e => e.stopPropagation()}
                    >
                      {f.url}
                    </a>
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => deleteFile(f.filename)}
                      className="text-gray-400 hover:text-red-500 transition-colors"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {files.length === 0 && !uploading && (
        <div className="text-center text-gray-400 text-sm mt-10">
          <Upload size={28} className="mx-auto mb-2" strokeWidth={1.5} />
          Файлов пока нет
        </div>
      )}
    </div>
  )
}
