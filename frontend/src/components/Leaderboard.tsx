import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLeaderboard } from '../api/client'
import type { LeaderboardEntry } from '../types'
import { getScoreBg } from '../types'

interface Props {
  repoId: number
}

const MEDAL = ['1st', '2nd', '3rd']

export default function Leaderboard({ repoId }: Props) {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    getLeaderboard(repoId)
      .then(setEntries)
      .catch(() => setError('Failed to load leaderboard'))
      .finally(() => setLoading(false))
  }, [repoId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-400">
        {error}
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-gray-400 dark:text-gray-500">
        No reviews yet — author rankings will appear here.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {['Rank', 'Author', 'PRs', 'Avg Overall', 'Avg Security', 'Avg Quality', 'Avg Req.', 'Avg Perf.'].map(
              (h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800 bg-white dark:bg-gray-900">
          {entries.map((e) => (
            <tr
              key={e.author}
              className={e.rank <= 3 ? 'bg-yellow-50/40 dark:bg-yellow-900/10' : ''}
            >
              <td className="px-4 py-3 text-sm font-bold text-gray-700 dark:text-gray-200">
                {MEDAL[e.rank - 1] ?? `#${e.rank}`}
              </td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                <Link
                  to={`/repos/${repoId}/authors/${encodeURIComponent(e.author)}`}
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  @{e.author}
                </Link>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{e.pr_count}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${getScoreBg(e.avg_overall)}`}
                >
                  {e.avg_overall.toFixed(1)}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {e.avg_security.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {e.avg_quality.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {e.avg_requirement.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                {e.avg_performance.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
