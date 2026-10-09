import { useEffect, useState } from 'react'
import { getBenchmark } from '../api/client'
import type { BenchmarkResult } from '../types'

interface Props {
  repoId: number
  score: number
}

export default function BenchmarkBadge({ repoId, score }: Props) {
  const [benchmark, setBenchmark] = useState<BenchmarkResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    getBenchmark(repoId, score)
      .then(setBenchmark)
      .catch(() => setBenchmark(null))
      .finally(() => setLoading(false))
  }, [repoId, score])

  if (loading) {
    return (
      <div className="animate-pulse inline-flex items-center rounded-full bg-blue-100 px-4 py-1.5 text-sm font-medium text-blue-800">
        Calculating benchmark…
      </div>
    )
  }

  if (!benchmark) return null

  const percentile = benchmark.percentile
  const color =
    percentile >= 75
      ? 'bg-green-100 text-green-800'
      : percentile >= 50
      ? 'bg-yellow-100 text-yellow-800'
      : 'bg-red-100 text-red-800'

  return (
    <div
      className={`inline-flex items-center gap-1.5 rounded-full px-4 py-1.5 text-sm font-medium ${color}`}
    >
      <span>
        Better than <strong>{percentile.toFixed(0)}%</strong> of PRs in this
        repository
      </span>
      <span className="text-xs opacity-70">
        ({benchmark.total_reviews} total)
      </span>
    </div>
  )
}
