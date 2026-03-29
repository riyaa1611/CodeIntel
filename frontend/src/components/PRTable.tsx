import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listReviews } from '../api/client'
import type { PaginatedPRReviews, PRReviewListItem } from '../types'
import { getScoreBg } from '../types'

interface Props {
  repoId: number
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <span className={`inline-block rounded-md px-2 py-0.5 text-xs font-semibold ${getScoreBg(score)}`}>
      {score.toFixed(0)}
    </span>
  )
}

export default function PRTable({ repoId }: Props) {
  const navigate = useNavigate()
  const [data, setData] = useState<PaginatedPRReviews | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)
  const [minScore, setMinScore] = useState<string>('')
  const [maxScore, setMaxScore] = useState<string>('')

  const fetchReviews = (p: number) => {
    setLoading(true)
    setError(null)
    listReviews(repoId, {
      page: p,
      limit: 20,
      min_score: minScore ? parseFloat(minScore) : undefined,
      max_score: maxScore ? parseFloat(maxScore) : undefined,
    })
      .then(setData)
      .catch(() => setError('Failed to load reviews'))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    setPage(1)
    fetchReviews(1)
  }, [repoId, minScore, maxScore])

  useEffect(() => {
    fetchReviews(page)
  }, [page])

  const handleRowClick = (review: PRReviewListItem) => {
    navigate(`/repos/${repoId}/reviews/${review.id}`)
  }

  return (
    <div>
      {/* Filters */}
      <div className="mb-4 flex items-center gap-3 flex-wrap">
        <span className="text-sm font-medium text-gray-600">Filter by score:</span>
        <input
          type="number"
          placeholder="Min score"
          value={minScore}
          onChange={(e) => setMinScore(e.target.value)}
          className="input w-28"
          min={0}
          max={100}
        />
        <span className="text-gray-400">–</span>
        <input
          type="number"
          placeholder="Max score"
          value={maxScore}
          onChange={(e) => setMaxScore(e.target.value)}
          className="input w-28"
          min={0}
          max={100}
        />
        {(minScore || maxScore) && (
          <button
            onClick={() => { setMinScore(''); setMaxScore('') }}
            className="text-sm text-blue-600 hover:underline"
          >
            Clear
          </button>
        )}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  {['PR #', 'Title', 'Author', 'Overall', 'Req.', 'Security', 'Quality', 'Perf.', 'Date'].map(
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
                {data.items.length === 0 && (
                  <tr>
                    <td colSpan={9} className="py-10 text-center text-sm text-gray-400">
                      No reviews found.
                    </td>
                  </tr>
                )}
                {data.items.map((r) => (
                  <tr
                    key={r.id}
                    onClick={() => handleRowClick(r)}
                    className="cursor-pointer hover:bg-blue-50 transition-colors"
                  >
                    <td className="px-4 py-3 text-sm font-medium text-blue-600">
                      #{r.pr_number}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                      {r.pr_title}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      @{r.pr_author}
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={r.score_overall} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={r.score_requirement} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={r.score_security} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={r.score_quality} />
                    </td>
                    <td className="px-4 py-3">
                      <ScoreBadge score={r.score_performance} />
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {new Date(r.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
              <span>
                {data.total} reviews · page {data.page} of {data.pages}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="btn-secondary px-3 py-1 text-xs disabled:opacity-40"
                >
                  ← Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                  className="btn-secondary px-3 py-1 text-xs disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
