import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getAuthorTrend } from '@/api/client'
import type { AuthorTrendPoint } from '@/types'

const SERIES = [
  { key: 'score_overall', label: 'Overall', color: '#2563eb' },
  { key: 'score_requirement', label: 'Requirement', color: '#16a34a' },
  { key: 'score_security', label: 'Security', color: '#dc2626' },
  { key: 'score_quality', label: 'Quality', color: '#d97706' },
  { key: 'score_performance', label: 'Performance', color: '#7c3aed' },
] as const

export default function AuthorTrend() {
  const { repoId, author } = useParams<{ repoId: string; author: string }>()
  const navigate = useNavigate()
  const decodedAuthor = author ? decodeURIComponent(author) : ''
  const [data, setData] = useState<AuthorTrendPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!repoId || !decodedAuthor) return
    setLoading(true)
    getAuthorTrend(Number(repoId), decodedAuthor)
      .then(setData)
      .catch(() => setError('Failed to load author trend data'))
      .finally(() => setLoading(false))
  }, [repoId, decodedAuthor])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="text-sm text-gray-500 hover:text-gray-800 dark:hover:text-gray-200 flex items-center gap-1"
            >
              ← Back
            </button>
            <span className="text-lg font-bold text-blue-600">CodeIntel</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="card">
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            Score Trend — @{decodedAuthor}
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Score evolution across {data.length} pull request{data.length !== 1 ? 's' : ''}
          </p>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-16">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
          </div>
        )}

        {error && (
          <div className="card border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
            <p className="text-red-700 dark:text-red-400">{error}</p>
          </div>
        )}

        {!loading && !error && data.length === 0 && (
          <div className="card text-center py-12 text-gray-500 dark:text-gray-400">
            No PR reviews found for this author yet.
          </div>
        )}

        {!loading && data.length > 0 && (
          <>
            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-4">
                Score Trajectory
              </h2>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: '#6b7280' }}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => [value.toFixed(1), name]}
                    labelFormatter={(label) => `Date: ${label}`}
                    contentStyle={{ fontSize: 12 }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  {SERIES.map(s => (
                    <Line
                      key={s.key}
                      type="monotone"
                      dataKey={s.key}
                      name={s.label}
                      stroke={s.color}
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-4">
                PR History
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-xs text-gray-500 uppercase tracking-wide">
                      <th className="pb-2 pr-4">PR</th>
                      <th className="pb-2 pr-4">Date</th>
                      <th className="pb-2 pr-4">Overall</th>
                      <th className="pb-2 pr-4">Req</th>
                      <th className="pb-2 pr-4">Sec</th>
                      <th className="pb-2 pr-4">Qual</th>
                      <th className="pb-2">Perf</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((row, i) => (
                      <tr key={i} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                        <td className="py-2 pr-4 text-blue-600 font-medium">#{row.pr_number}</td>
                        <td className="py-2 pr-4 text-gray-500">{row.date}</td>
                        <td className="py-2 pr-4 font-semibold">{row.score_overall.toFixed(1)}</td>
                        <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{row.score_requirement.toFixed(1)}</td>
                        <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{row.score_security.toFixed(1)}</td>
                        <td className="py-2 pr-4 text-gray-600 dark:text-gray-400">{row.score_quality.toFixed(1)}</td>
                        <td className="py-2 text-gray-600 dark:text-gray-400">{row.score_performance.toFixed(1)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  )
}
