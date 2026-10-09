import { useEffect, useState } from 'react'
import { getRepoStats } from '../api/client'
import type { RepoStats } from '../types'
import TrendChart from './TrendChart'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

interface Props {
  repoId: number
}

function StatCard({
  label,
  value,
  sub,
  color,
}: {
  label: string
  value: string | number
  sub?: string
  color?: string
}) {
  return (
    <div className="card">
      <p className="text-sm font-medium text-gray-500">{label}</p>
      <p className={`mt-1 text-3xl font-bold ${color ?? 'text-gray-900 dark:text-gray-100'}`}>
        {value}
      </p>
      {sub && <p className="mt-0.5 text-xs text-gray-400">{sub}</p>}
    </div>
  )
}

export default function Dashboard({ repoId }: Props) {
  const [stats, setStats] = useState<RepoStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getRepoStats(repoId)
      .then(setStats)
      .catch(() => setError('Failed to load stats'))
      .finally(() => setLoading(false))
  }, [repoId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="h-7 w-7 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
        {error}
      </div>
    )
  }

  if (!stats) return null

  if (stats.total_reviews === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300">No PRs reviewed yet</h3>
        <p className="text-sm text-gray-500 mt-1">Open a pull request on this repo and CodeIntel will automatically review it.</p>
      </div>
    )
  }

  const { dimension_averages: da, score_distribution: sd } = stats
  const criticalCount = sd.low
  const avgColor =
    da.avg_overall >= 70
      ? 'text-green-600'
      : da.avg_overall >= 40
      ? 'text-yellow-600'
      : 'text-red-600'

  const distData = [
    { name: '0–40 (Low)', count: sd.low, fill: '#ef4444' },
    { name: '41–70 (Med)', count: sd.medium, fill: '#f59e0b' },
    { name: '71–100 (High)', count: sd.high, fill: '#22c55e' },
  ]

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard
          label="Total PRs Reviewed"
          value={stats.total_reviews}
          sub="all time"
        />
        <StatCard
          label="Average Score"
          value={`${da.avg_overall.toFixed(1)}/100`}
          color={avgColor}
          sub="overall"
        />
        <StatCard
          label="Critical PRs"
          value={criticalCount}
          color={criticalCount > 0 ? 'text-red-600' : 'text-green-600'}
          sub="score ≤ 40"
        />
      </div>

      {/* Dimension averages */}
      <div className="card">
        <h3 className="mb-4 text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Average Scores by Dimension
        </h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: 'Requirement', val: da.avg_requirement },
            { label: 'Security', val: da.avg_security },
            { label: 'Quality', val: da.avg_quality },
            { label: 'Performance', val: da.avg_performance },
          ].map(({ label, val }) => (
            <div key={label} className="text-center">
              <div
                className={`text-2xl font-bold ${
                  val >= 70
                    ? 'text-green-600'
                    : val >= 40
                    ? 'text-yellow-600'
                    : 'text-red-600'
                }`}
              >
                {val.toFixed(1)}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 uppercase tracking-wide">
            30-Day Score Trend
          </h3>
          <TrendChart data={stats.trend_data} />
        </div>

        <div className="card">
          <h3 className="mb-4 text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Score Distribution
          </h3>
          {stats.total_reviews === 0 ? (
            <div className="flex h-48 items-center justify-center text-sm text-gray-400">
              No data yet
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart
                data={distData}
                margin={{ top: 5, right: 10, bottom: 5, left: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#6b7280' }}
                  tickLine={false}
                  axisLine={false}
                  width={25}
                  allowDecimals={false}
                />
                <Tooltip
                  formatter={(v: number) => [v, 'PRs']}
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {distData.map((entry, index) => (
                    <Cell key={index} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
