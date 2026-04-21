import { useState, useEffect } from 'react'
import { Users, Activity, Clock, TrendingUp } from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'
import api from '../api/axios'

const LEVELS = { 1:'Start', 2:'Return', 3:'Base', 4:'Stability' }

function MetricCard({ icon: Icon, value, label, color = 'violet' }) {
  const colors = {
    violet: 'bg-violet-100 text-violet-600',
    green:  'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    blue:   'bg-blue-100 text-blue-600',
  }
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-4 ${colors[color]}`}>
        <Icon size={20} />
      </div>
      {value == null
        ? <div className="h-9 w-16 bg-gray-100 rounded animate-pulse mb-1" />
        : <div className="text-3xl font-bold text-gray-900">{value}</div>
      }
      <div className="text-sm text-gray-500 mt-1">{label}</div>
    </div>
  )
}

export default function Analytics() {
  const [summary, setSummary] = useState(null)
  const [chart, setChart]     = useState([])
  const [byLevel, setByLevel] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const [s, c, l] = await Promise.all([
          api.get('/analytics/summary'),
          api.get('/analytics/completion-chart'),
          api.get('/analytics/by-level'),
        ])
        setSummary(s.data)
        setChart(c.data)
        setByLevel(l.data)
      } catch (e) { console.error(e) }
      finally { setLoading(false) }
    }
    load()
  }, [])

  return (
    <div>
      <div className="border-b border-gray-200 pb-4 mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Аналитика</h1>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <MetricCard icon={Users}     value={summary?.total_users}   label="Всего пользователей"      color="violet" />
        <MetricCard icon={Activity}  value={summary?.active_users}  label="Активных"                  color="green"  />
        <MetricCard icon={Clock}     value={summary?.pending_users} label="Ожидают подтверждения"     color="yellow" />
        <MetricCard icon={TrendingUp}
          value={summary?.avg_completion_7d != null ? `${summary.avg_completion_7d}%` : null}
          label="Среднее выполнение за 7 дней"
          color="blue"
        />
      </div>

      {/* Chart */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <h2 className="text-sm font-semibold text-gray-900 mb-5">Выполнение за последние 14 дней</h2>
        {loading ? (
          <div className="h-52 bg-gray-100 rounded-lg animate-pulse" />
        ) : chart.length === 0 ? (
          <div className="h-52 flex items-center justify-center text-gray-400 text-sm">Нет данных</div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chart} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#9ca3af' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 12 }}
                labelStyle={{ fontWeight: 600 }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="done"    name="Выполнено" stroke="#16a34a" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="partial" name="Частично"  stroke="#ca8a04" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              <Line type="monotone" dataKey="skipped" name="Пропущено" stroke="#dc2626" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* By level table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900">По уровням</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              {['Уровень','Пользователей','Активных','Среднее выполнение','Avg день программы'].map(h => (
                <th key={h} className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 4 }).map((_, i) => (
                <tr key={i} className="border-b border-gray-100">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <td key={j} className="px-5 py-3"><div className="h-4 bg-gray-100 rounded animate-pulse w-16" /></td>
                  ))}
                </tr>
              ))
              : byLevel.length === 0
                ? <tr><td colSpan={5} className="px-5 py-10 text-center text-gray-400 text-sm">Нет данных</td></tr>
                : byLevel.map(row => (
                  <tr key={row.level} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-5 py-3 font-medium text-gray-900">{row.level} — {LEVELS[row.level] || row.name}</td>
                    <td className="px-5 py-3 text-gray-700">{row.total}</td>
                    <td className="px-5 py-3 text-gray-700">{row.active}</td>
                    <td className="px-5 py-3 text-gray-700">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 bg-gray-100 rounded-full h-1.5 max-w-24">
                          <div
                            className="bg-violet-500 h-1.5 rounded-full"
                            style={{ width: `${Math.min(row.avg_completion, 100)}%` }}
                          />
                        </div>
                        <span>{row.avg_completion}%</span>
                      </div>
                    </td>
                    <td className="px-5 py-3 text-gray-700">{row.avg_day ? Math.round(row.avg_day) : '—'}</td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>
    </div>
  )
}
