import { useEffect, useState } from 'react'
import { getReviewDiff } from '@/api/client'

interface Props {
  repoId: number
  reviewId: number
}

function classForLine(line: string): string {
  if (line.startsWith('+') && !line.startsWith('+++')) return 'bg-green-50 text-green-900 dark:bg-green-950/40 dark:text-green-200'
  if (line.startsWith('-') && !line.startsWith('---')) return 'bg-red-50 text-red-900 dark:bg-red-950/40 dark:text-red-200'
  if (line.startsWith('@@')) return 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300'
  if (line.startsWith('diff ') || line.startsWith('index ') || line.startsWith('---') || line.startsWith('+++'))
    return 'text-gray-500 dark:text-gray-400 font-semibold'
  return 'text-gray-700 dark:text-gray-300'
}

export default function PRDiffViewer({ repoId, reviewId }: Props) {
  const [diff, setDiff] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (!open || diff !== null) return
    setLoading(true)
    setError(null)
    getReviewDiff(repoId, reviewId)
      .then(setDiff)
      .catch(() => setError('Failed to load diff from GitHub'))
      .finally(() => setLoading(false))
  }, [open, repoId, reviewId, diff])

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(v => !v)}
        className="w-full flex items-center justify-between px-5 py-4 text-left bg-white dark:bg-gray-900 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        <span className="font-medium text-gray-800 dark:text-gray-200">PR Diff</span>
        <span className="text-gray-400 text-lg">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="border-t border-gray-100 dark:border-gray-700">
          {loading && (
            <div className="flex items-center justify-center py-8">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            </div>
          )}
          {error && (
            <div className="px-5 py-4 text-sm text-red-600 dark:text-red-400">{error}</div>
          )}
          {diff && !loading && (
            <div className="overflow-x-auto">
              <pre className="text-xs font-mono leading-5 p-4 bg-gray-50 dark:bg-gray-950">
                {diff.split('\n').map((line, i) => (
                  <div key={i} className={`px-1 ${classForLine(line)}`}>
                    {line || ' '}
                  </div>
                ))}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
