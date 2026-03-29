import { useEffect, useState } from 'react'
import { getLeaderboard } from '../api/client'
import type { LeaderboardEntry } from '../types'
import { getScoreBg } from '../types'

interface Props {
  repoId: number
}

const MEDAL = ['🥇', '🥈', '🥉']

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
      <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
        {error}
      </div>
    )
  }

  if (entries.length === 0) {
    return (
      <div className="py-10 text-center text-sm text-gray-400">
        No reviews yet — author rankings will appear here.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {['Rank', 'Author', 'PRs', 'Avg Overall', 'Avg Security', 'Avg Quality', 'Avg Req.', 'Avg Perf.'].map(
              (h) => (
                <th
                  key={h}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide"
                >
                  {h}
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 bg-white">
          {entries.map((e) => (
            <tr
              key={e.author}
              className={e.rank <= 3 ? 'bg-yellow-50/40' : ''}
            >
              <td className="px-4 py-3 text-sm font-bold text-gray-700">
                {MEDAL[e.rank - 1] ?? `#${e.rank}`}
              </td>
              <td className="px-4 py-3 text-sm font-medium text-gray-900">
                @{e.author}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">{e.pr_count}</td>
              <td className="px-4 py-3">
                <span
                  className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${getScoreBg(e.avg_overall)}`}
                >
                  {e.avg_overall.toFixed(1)}
                </span>
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {e.avg_security.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {e.avg_quality.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {e.avg_requirement.toFixed(1)}
              </td>
              <td className="px-4 py-3 text-sm text-gray-600">
                {e.avg_performance.toFixed(1)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
