import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Search, Star, GitFork, AlertCircle, Eye, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react'
import { getPublicRepo } from '../api/client'
import type { PublicRepoData } from '../types'

// ── Language palette ──────────────────────────────────────────────────────────
const LANG_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#f97316', '#84cc16', '#ec4899', '#6366f1',
]

function relativeTime(dateStr: string): string {
  if (!dateStr) return 'Unknown'
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return `${diff} seconds ago`
  if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`
  if (diff < 2592000) return `${Math.floor(diff / 86400)} days ago`
  if (diff < 31536000) return `${Math.floor(diff / 2592000)} months ago`
  return `${Math.floor(diff / 31536000)} years ago`
}

function HealthRing({ score }: { score: number }) {
  const radius = 44
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="120" height="120" className="-rotate-90">
        <circle cx="60" cy="60" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
      </svg>
      <div className="absolute flex flex-col items-center justify-center" style={{ marginTop: '-80px' }}>
        <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        <span className="text-xs text-gray-500">/ 100</span>
      </div>
    </div>
  )
}

function HealthScoreCard({ score }: { score: number }) {
  const color = score >= 75 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'
  const bg = score >= 75 ? 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800' : score >= 50 ? 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-800' : 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800'
  const label = score >= 75 ? 'Healthy' : score >= 50 ? 'Fair' : 'Needs Work'

  const radius = 44
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference
  const strokeColor = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'

  return (
    <div className={`border rounded-xl p-4 ${bg} flex flex-col items-center gap-2 min-w-[140px]`}>
      <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Health Score</p>
      <div className="relative flex items-center justify-center">
        <svg width="110" height="110" className="-rotate-90">
          <circle cx="55" cy="55" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="10" />
          <circle
            cx="55"
            cy="55"
            r={radius}
            fill="none"
            stroke={strokeColor}
            strokeWidth="10"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
          />
        </svg>
        <div className="absolute flex flex-col items-center">
          <span className={`text-2xl font-bold ${color}`}>{score}</span>
          <span className="text-xs text-gray-500 dark:text-gray-400">/ 100</span>
        </div>
      </div>
      <span className={`text-sm font-semibold ${color}`}>{label}</span>
    </div>
  )
}

function LanguageBar({ languages, percentages }: { languages: Record<string, number>; percentages: Record<string, number> }) {
  const entries = Object.entries(percentages).sort((a, b) => b[1] - a[1]).slice(0, 8)
  if (entries.length === 0) return null

  const chartData = entries.map(([lang, pct], i) => ({
    name: lang,
    value: pct,
    color: LANG_COLORS[i % LANG_COLORS.length],
  }))

  return (
    <div>
      <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-2">Languages</p>
      {/* Stacked bar */}
      <div className="flex rounded-full overflow-hidden h-3 mb-3">
        {chartData.map(({ name, value, color }) => (
          <div
            key={name}
            style={{ width: `${value}%`, backgroundColor: color }}
            title={`${name}: ${value}%`}
          />
        ))}
      </div>
      {/* Legend */}
      <div className="flex flex-wrap gap-x-4 gap-y-1">
        {chartData.map(({ name, value, color }) => (
          <div key={name} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full inline-block flex-shrink-0" style={{ backgroundColor: color }} />
            <span className="text-xs text-gray-600 dark:text-gray-300">{name}</span>
            <span className="text-xs text-gray-400 dark:text-gray-500">{value}%</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ContributorList({ contributors }: { contributors: PublicRepoData['contributors'] }) {
  const [expanded, setExpanded] = useState(false)
  const visible = expanded ? contributors : contributors.slice(0, 5)

  return (
    <div>
      <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-2">Top Contributors</p>
      <div className="space-y-1.5">
        {visible.map((c) => (
          <div key={c.login} className="flex items-center gap-2">
            <img
              src={c.avatar_url || `https://github.com/${c.login}.png?size=32`}
              alt={c.login}
              className="w-6 h-6 rounded-full border border-gray-200 dark:border-gray-700"
            />
            <a
              href={`https://github.com/${c.login}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:underline flex-1 truncate"
            >
              {c.login}
            </a>
            <span className="text-xs text-gray-500 dark:text-gray-400 tabular-nums">{c.contributions} commits</span>
          </div>
        ))}
      </div>
      {contributors.length > 5 && (
        <button
          onClick={() => setExpanded((v) => !v)}
          className="mt-2 text-xs text-blue-600 hover:underline flex items-center gap-1"
        >
          {expanded ? (
            <><ChevronUp className="w-3 h-3" /> Show less</>
          ) : (
            <><ChevronDown className="w-3 h-3" /> Show {contributors.length - 5} more</>
          )}
        </button>
      )}
    </div>
  )
}

function RepoResultCard({ data }: { data: PublicRepoData }) {
  const repoAge = Math.floor((Date.now() - new Date(data.created_at).getTime()) / (1000 * 60 * 60 * 24 * 365))
  const ageLabel = repoAge === 0 ? 'Created this year' : `${repoAge}y old`

  return (
    <div className="card mt-4 space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex-1 min-w-0 space-y-3">
          {/* Title row */}
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{data.full_name}</h3>
            <a
              href={`https://github.com/${data.full_name}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 rounded-lg text-xs font-medium transition-colors"
            >
              <ExternalLink className="w-3 h-3" />View on GitHub
            </a>
            {data.homepage && (
              <a href={data.homepage} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-50 dark:bg-blue-900/30 hover:bg-blue-100 dark:hover:bg-blue-900/50 text-blue-600 dark:text-blue-300 rounded-lg text-xs font-medium transition-colors">
                <ExternalLink className="w-3 h-3" />Live site
              </a>
            )}
          </div>

          {/* Description */}
          {data.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{data.description}</p>
          )}

          {/* Quick-info chips */}
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-300">
              Public
            </span>
            {data.language && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-300">
                {data.language}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-300">
              Branch: {data.default_branch}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-300">
              Active {relativeTime(data.pushed_at)}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-lg text-xs text-gray-600 dark:text-gray-300">
              {ageLabel}
            </span>
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-purple-50 dark:bg-purple-900/30 rounded-lg text-xs text-purple-600 dark:text-purple-300">
              {data.commits_last_30_days} commits / 30d
            </span>
          </div>

          {/* Topics */}
          {data.topics.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {data.topics.map((t) => (
                <span key={t} className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded-full text-xs font-medium">
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
        <HealthScoreCard score={data.health_score} />
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { icon: Star, label: 'Stars', value: data.stars.toLocaleString(), color: 'text-yellow-500' },
          { icon: GitFork, label: 'Forks', value: data.forks.toLocaleString(), color: 'text-blue-500' },
          { icon: AlertCircle, label: 'Issues', value: data.open_issues.toLocaleString(), color: 'text-red-400' },
          { icon: Eye, label: 'Watchers', value: data.watchers.toLocaleString(), color: 'text-green-500' },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 flex items-center gap-2">
            <Icon className={`w-4 h-4 ${color}`} />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
              <p className="font-semibold text-gray-800 dark:text-gray-100 text-sm">{value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Language breakdown */}
      {Object.keys(data.language_percentages).length > 0 && (
        <LanguageBar languages={data.languages} percentages={data.language_percentages} />
      )}

      {/* Contributors + metadata */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {data.contributors.length > 0 && (
          <ContributorList contributors={data.contributors} />
        )}
        <div className="space-y-2 text-sm">
          <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide">Details</p>
          {data.license && (
            <div className="flex justify-between">
              <span className="text-gray-500">License</span>
              <span className="font-medium text-gray-700 dark:text-gray-300">{data.license}</span>
            </div>
          )}
          {data.language && (
            <div className="flex justify-between">
              <span className="text-gray-500">Primary language</span>
              <span className="font-medium text-gray-700 dark:text-gray-300">{data.language}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span className="text-gray-500">Commits (30d)</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{data.commits_last_30_days}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Default branch</span>
            <span className="font-mono text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-gray-700 dark:text-gray-300">{data.default_branch}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Last active</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{relativeTime(data.pushed_at)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="card mt-4 space-y-4 animate-pulse">
      <div className="flex gap-4">
        <div className="flex-1 space-y-2">
          <div className="h-5 bg-gray-200 rounded w-1/2" />
          <div className="h-4 bg-gray-200 rounded w-3/4" />
          <div className="flex gap-2 mt-2">
            {[1, 2, 3].map((i) => <div key={i} className="h-5 w-14 bg-gray-200 rounded-full" />)}
          </div>
        </div>
        <div className="w-24 h-24 bg-gray-200 rounded-xl" />
      </div>
      <div className="grid grid-cols-4 gap-3">
        {[1, 2, 3, 4].map((i) => <div key={i} className="h-14 bg-gray-200 rounded-lg" />)}
      </div>
      <div className="h-4 bg-gray-200 rounded w-full" />
      <div className="h-4 bg-gray-200 rounded w-5/6" />
    </div>
  )
}

interface PublicRepoSearchProps {
  repoFullName?: string | null
}

export default function PublicRepoSearch({ repoFullName }: PublicRepoSearchProps = {}) {
  const [query, setQuery] = useState('')
  const [data, setData] = useState<PublicRepoData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchRepo = async (ownerRepo: string) => {
    const parts = ownerRepo.split('/')
    if (parts.length !== 2 || !parts[0] || !parts[1]) return
    const [owner, repo] = parts
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await getPublicRepo(owner, repo)
      setData(result)
    } catch (err: any) {
      const status = err?.response?.status
      if (status === 404) setError(`Repository "${ownerRepo}" not found`)
      else if (status === 429) setError('GitHub API rate limit exceeded. Try again in a moment.')
      else setError('Failed to fetch repository data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // Auto-fetch when a registered repo is selected
  useEffect(() => {
    if (repoFullName) {
      setQuery(repoFullName)
      fetchRepo(repoFullName)
    }
  }, [repoFullName])

  const handleSearch = async () => {
    let trimmed = query.trim()
    if (!trimmed) return
    const urlMatch = trimmed.match(/github\.com\/([^/]+)\/([^/]+?)(?:\.git)?\/?$/)
    if (urlMatch) trimmed = `${urlMatch[1]}/${urlMatch[2]}`
    const parts = trimmed.split('/')
    if (parts.length !== 2 || !parts[0] || !parts[1]) {
      setError('Please enter a valid owner/repo format (e.g. facebook/react)')
      return
    }
    fetchRepo(trimmed)
  }

  return (
    <div className="mb-8">
      <div className="card">
        <h2 className="text-base font-semibold text-gray-800 mb-1 dark:text-gray-100">Repository Analytics</h2>
        <p className="text-sm text-gray-500 mb-4">
          {repoFullName ? `Showing analytics for ${repoFullName}` : 'Instantly analyze any public GitHub repository — no connection required.'}
        </p>
        {!repoFullName && (
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="owner/repo or full GitHub URL"
              className="input pl-9 w-full"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="btn-primary whitespace-nowrap"
          >
            {loading ? 'Analyzing…' : 'Analyze'}
          </button>
        </div>
        )}
        {loading && repoFullName && (
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
            Analyzing {repoFullName}…
          </div>
        )}

        {error && (
          <div className="mt-3 flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            {error}
          </div>
        )}
      </div>

      {loading && <SkeletonCard />}
      {data && <RepoResultCard data={data} />}
    </div>
  )
}
