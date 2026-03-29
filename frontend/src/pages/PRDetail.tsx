import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getReview } from '../api/client'
import type { PRReview } from '../types'
import { getScoreBg, getScoreEmoji } from '../types'
import BenchmarkBadge from '../components/BenchmarkBadge'
import RadarChart from '../components/RadarChart'

function ScorePill({ score }: { score: number }) {
  return (
    <span
      className={`inline-block rounded-full px-3 py-1 text-sm font-semibold ${getScoreBg(score)}`}
    >
      {getScoreEmoji(score)} {score.toFixed(0)}/100
    </span>
  )
}

function Section({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-4 text-left bg-white hover:bg-gray-50 transition-colors"
      >
        <span className="font-medium text-gray-800">{title}</span>
        <span className="text-gray-400 text-lg">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-5 py-4 border-t border-gray-100 bg-gray-50 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {children}
        </div>
      )}
    </div>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const copy = () => {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  }
  return (
    <button
      onClick={copy}
      className="ml-2 text-xs text-blue-500 hover:text-blue-700"
    >
      {copied ? '✓ Copied' : 'Copy'}
    </button>
  )
}

export default function PRDetail() {
  const { repoId, reviewId } = useParams<{ repoId: string; reviewId: string }>()
  const navigate = useNavigate()
  const [review, setReview] = useState<PRReview | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!repoId || !reviewId) return
    setLoading(true)
    getReview(Number(repoId), Number(reviewId))
      .then(setReview)
      .catch(() => setError('Failed to load review'))
      .finally(() => setLoading(false))
  }, [repoId, reviewId])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
      </div>
    )
  }

  if (error || !review) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-700">
          {error ?? 'Review not found'}
        </div>
        <button onClick={() => navigate(-1)} className="btn-secondary">
          ← Back
        </button>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
            >
              ← Back
            </button>
            <span className="text-lg font-bold text-blue-600">🤖 CodeIntel</span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* PR Header */}
        <div className="card">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-medium text-blue-600 uppercase tracking-wide mb-1">
                Pull Request #{review.pr_number}
              </p>
              <h1 className="text-xl font-bold text-gray-900">
                {review.pr_title}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                by @{review.pr_author} ·{' '}
                {new Date(review.created_at).toLocaleString()}
              </p>
            </div>
            <div className="flex flex-col items-end gap-2">
              <ScorePill score={review.score_overall} />
              <span className="text-xs text-gray-400 font-mono">
                {review.head_sha.slice(0, 8)}
              </span>
            </div>
          </div>

          <div className="mt-4">
            <BenchmarkBadge
              repoId={Number(repoId)}
              score={review.score_overall}
            />
          </div>
        </div>

        {/* Scores + Radar */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Dimension scores */}
          <div className="card space-y-3">
            <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Dimension Scores
            </h2>
            {[
              { label: '✅ Requirement Alignment', score: review.score_requirement },
              { label: '🔒 Security', score: review.score_security },
              { label: '🏗️ Code Quality', score: review.score_quality },
              { label: '⚡ Performance', score: review.score_performance },
            ].map(({ label, score }) => (
              <div key={label} className="flex items-center justify-between">
                <span className="text-sm text-gray-700">{label}</span>
                <ScorePill score={score} />
              </div>
            ))}
          </div>

          {/* Radar chart */}
          <div className="card">
            <h2 className="mb-2 text-sm font-semibold text-gray-700 uppercase tracking-wide">
              Score Radar
            </h2>
            <RadarChart
              scoreRequirement={review.score_requirement}
              scoreSecurity={review.score_security}
              scoreQuality={review.score_quality}
              scorePerformance={review.score_performance}
            />
          </div>
        </div>

        {/* Critical Issues */}
        {review.critical_issues.length > 0 && (
          <div className="card border-red-200 bg-red-50">
            <h2 className="mb-3 text-sm font-semibold text-red-700 uppercase tracking-wide">
              🚨 Critical Issues
            </h2>
            <ul className="space-y-2">
              {review.critical_issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-red-800">
                  <span className="mt-0.5 text-red-500">●</span>
                  {issue}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Warnings */}
        {review.warnings.length > 0 && (
          <div className="card border-yellow-200 bg-yellow-50">
            <h2 className="mb-3 text-sm font-semibold text-yellow-700 uppercase tracking-wide">
              ⚠️ Warnings
            </h2>
            <ul className="space-y-2">
              {review.warnings.map((w, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-yellow-800">
                  <span className="mt-0.5 text-yellow-500">●</span>
                  {w}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Dimension Feedback */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
            Detailed Feedback
          </h2>
          <Section title="✅ Requirement Alignment" defaultOpen>
            {review.feedback_requirement}
          </Section>
          <Section title="🔒 Security">
            {review.feedback_security}
          </Section>
          <Section title="🏗️ Code Quality">
            {review.feedback_quality}
          </Section>
          <Section title="⚡ Performance">
            {review.feedback_performance}
          </Section>
        </div>

        {/* Test Suggestions */}
        {review.test_suggestions.length > 0 && (
          <div className="card">
            <h2 className="mb-3 text-sm font-semibold text-gray-700 uppercase tracking-wide">
              🧪 Suggested Test Cases
            </h2>
            <ul className="space-y-2">
              {review.test_suggestions.map((suggestion, i) => (
                <li
                  key={i}
                  className="flex items-start justify-between gap-4 rounded-lg bg-gray-50 px-4 py-3 text-sm text-gray-700"
                >
                  <span>
                    <span className="font-semibold text-gray-500 mr-2">
                      {i + 1}.
                    </span>
                    {suggestion}
                  </span>
                  <CopyButton text={suggestion} />
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-gray-400 py-4">
          CodeIntel AI Review · Re-trigger by commenting{' '}
          <code className="bg-gray-100 px-1 rounded">/codeintel review</code> on
          the PR
        </div>
      </main>
    </div>
  )
}
