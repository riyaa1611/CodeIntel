import { useCallback, useEffect, useState } from 'react'
import { createRepo, listRepos } from '../api/client'
import type { Repository } from '../types'
import Dashboard from '../components/Dashboard'
import PRTable from '../components/PRTable'
import Leaderboard from '../components/Leaderboard'
import SlackSetup from '../components/SlackSetup'
import ScoringWeightsSliders from '../components/ScoringWeightsSliders'
import ScanScheduler from '../components/ScanScheduler'
import ExportPanel from '../components/ExportPanel'
import PublicRepoSearch from '../components/PublicRepoSearch'
import DeepScanPanel from '../components/DeepScanPanel'
import RepositoryPreview from '../components/RepositoryPreview'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { useWebSocket, type WsEvent } from '@/hooks/useWebSocket'
import DarkModeToggle from '@/components/DarkModeToggle'

type Tab = 'overview' | 'reviews' | 'leaderboard' | 'settings' | 'deep_scan'

export default function Home() {
  const { user, logout } = useAuth()
  const { addToast } = useToast()

  const handleWsEvent = useCallback((event: WsEvent) => {
    if (event.type === 'review.completed') {
      const d = event.data as { pr_number: number; score_overall: number; repo_full_name: string }
      addToast('success', `PR #${d.pr_number} reviewed`, `${d.repo_full_name} — score ${d.score_overall.toFixed(1)}`)
    } else if (event.type === 'scan.progress') {
      addToast('info', 'Deep scan running', `Analyzing ${event.data.files_fetched as number} files…`)
    } else if (event.type === 'scan.completed') {
      const d = event.data as { overall_score: number; repo: string }
      addToast('success', 'Deep scan complete', `${d.repo} — score ${d.overall_score.toFixed(1)}`)
    }
  }, [addToast])

  useWebSocket(handleWsEvent)

  const [repos, setRepos] = useState<Repository[]>([])
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null)
  const [reposLoading, setReposLoading] = useState(true)
  const [reposError, setReposError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('overview')

  // Add repo form state
  const [showAddRepo, setShowAddRepo] = useState(false)
  const [newRepoName, setNewRepoName] = useState('')
  const [newSlackUrl, setNewSlackUrl] = useState('')
  const [addingRepo, setAddingRepo] = useState(false)
  const [addRepoError, setAddRepoError] = useState<string | null>(null)

  useEffect(() => {
    setReposLoading(true)
    listRepos()
      .then((data) => {
        setRepos(data)
        if (data.length > 0 && !selectedRepo) {
          setSelectedRepo(data[0])
        }
      })
      .catch(() => setReposError('Failed to load repositories'))
      .finally(() => setReposLoading(false))
  }, [])

  const handleAddRepo = async () => {
    if (!newRepoName.trim()) return
    // Accept full GitHub URLs
    let repoName = newRepoName.trim()
    const urlMatch = repoName.match(/github\.com\/([^/]+\/[^/]+?)(?:\.git)?\/?$/)
    if (urlMatch) repoName = urlMatch[1]

    if (!/^[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+$/.test(repoName)) {
      setAddRepoError('Please enter in owner/repo format (e.g. riyaa1611/CodeIntel)')
      return
    }

    setAddingRepo(true)
    setAddRepoError(null)
    try {
      const repo = await createRepo({
        github_repo_full_name: repoName,
        slack_webhook_url: newSlackUrl.trim() || undefined,
      })
      setRepos((prev) => [repo, ...prev])
      setSelectedRepo(repo)
      setNewRepoName('')
      setNewSlackUrl('')
      setShowAddRepo(false)
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      const msg = Array.isArray(detail)
        ? 'Invalid input: ' + detail.map((d: any) => d.msg).join(', ')
        : typeof detail === 'string'
        ? detail
        : 'Failed to add repository'
      setAddRepoError(msg)
    } finally {
      setAddingRepo(false)
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'reviews', label: 'PR Reviews' },
    { id: 'leaderboard', label: 'Leaderboard' },
    { id: 'deep_scan', label: 'Deep Scan' },
    { id: 'settings', label: 'Settings' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10 dark:bg-gray-900 dark:border-gray-700">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-blue-600">CodeIntel</span>
              <span className="hidden text-sm text-gray-400 sm:block">
                AI PR Review Dashboard
              </span>
            </div>

            <div className="flex items-center gap-3">
              {/* Repo selector */}
              {reposLoading ? (
                <div className="h-8 w-40 animate-pulse rounded bg-gray-200" />
              ) : reposError ? (
                <span className="text-xs text-red-500">{reposError}</span>
              ) : (
                <select
                  value={selectedRepo?.id ?? ''}
                  onChange={(e) => {
                    const repo = repos.find((r) => r.id === Number(e.target.value))
                    if (repo) {
                      setSelectedRepo(repo)
                      setActiveTab('overview')
                    }
                  }}
                  className="input w-56 text-sm"
                >
                  {repos.length === 0 && (
                    <option value="" disabled>
                      No repositories yet
                    </option>
                  )}
                  {repos.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.full_name}
                    </option>
                  ))}
                </select>
              )}

              <button
                onClick={() => setShowAddRepo((v) => !v)}
                className="btn-secondary text-sm"
              >
                {showAddRepo ? 'Cancel' : '+ Add Repo'}
              </button>

              <div className="flex items-center gap-3">
                <DarkModeToggle />
                {user?.avatar_url && (
                  <img src={user.avatar_url} alt={user.username}
                    className="w-8 h-8 rounded-full border border-gray-200" />
                )}
                <span className="text-sm text-gray-600 dark:text-gray-300">{user?.username}</span>
                <button onClick={logout}
                  className="text-sm text-red-500 hover:text-red-700 transition">
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Add repo form */}
      {showAddRepo && (
        <div className="bg-blue-50 dark:bg-gray-900 border-b border-blue-100 dark:border-gray-700/50">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-56">
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
                  GitHub Repo (owner/name)
                </label>
                <input
                  type="text"
                  placeholder="e.g. octocat/hello-world"
                  value={newRepoName}
                  onChange={(e) => setNewRepoName(e.target.value)}
                  className="input"
                  onKeyDown={(e) => e.key === 'Enter' && handleAddRepo()}
                />
              </div>
              <div className="flex-1 min-w-56">
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-300 mb-1">
                  Slack Webhook URL (optional)
                </label>
                <input
                  type="url"
                  placeholder="https://hooks.slack.com/services/..."
                  value={newSlackUrl}
                  onChange={(e) => setNewSlackUrl(e.target.value)}
                  className="input"
                />
              </div>
              <button
                onClick={handleAddRepo}
                disabled={addingRepo || !newRepoName.trim()}
                className="btn-primary"
              >
                {addingRepo ? 'Adding…' : 'Add Repository'}
              </button>
            </div>
            {addRepoError && (
              <p className="mt-2 text-sm text-red-600">{addRepoError}</p>
            )}
          </div>
        </div>
      )}

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6">
        {/* Public Repo Search — auto-loads selected repo analytics */}
        <PublicRepoSearch repoFullName={selectedRepo?.full_name ?? null} />

        {!selectedRepo ? (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <h2 className="text-xl font-semibold text-gray-700">
              Welcome to CodeIntel
            </h2>
            <p className="mt-2 text-gray-500 max-w-sm">
              Add a GitHub repository above to start seeing AI-powered PR review
              analytics.
            </p>
          </div>
        ) : (
          <>
            {/* Repo title */}
            <div className="mb-6">
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                {selectedRepo.full_name}
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                Connected since{' '}
                {new Date(selectedRepo.created_at).toLocaleDateString()}
              </p>
            </div>

            {/* Tabs */}
            <div className="mb-6 border-b border-gray-200">
              <nav className="-mb-px flex space-x-6">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab content */}
            {activeTab === 'overview' && (
              <div className="space-y-6">
                <Dashboard repoId={selectedRepo.id} />
                <RepositoryPreview repoId={selectedRepo.id} />
              </div>
            )}

            {activeTab === 'reviews' && (
              <div className="card">
                <h2 className="mb-4 text-base font-semibold text-gray-800">
                  Pull Request Reviews
                </h2>
                <PRTable repoId={selectedRepo.id} />
              </div>
            )}

            {activeTab === 'leaderboard' && (
              <div className="card">
                <h2 className="mb-4 text-base font-semibold text-gray-800">
                  Author Leaderboard
                </h2>
                <Leaderboard repoId={selectedRepo.id} />
              </div>
            )}

            {activeTab === 'deep_scan' && (
              <div className="card">
                <DeepScanPanel repoId={selectedRepo.id} />
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6 max-w-2xl">
                <div className="card">
                  <h2 className="mb-4 text-base font-semibold text-gray-800 dark:text-gray-100">
                    Slack Notifications
                  </h2>
                  <SlackSetup
                    repoId={selectedRepo.id}
                    currentWebhook={selectedRepo.slack_webhook_url}
                    onUpdated={(url) =>
                      setSelectedRepo((r) =>
                        r ? { ...r, slack_webhook_url: url } : r
                      )
                    }
                  />
                </div>
                <div className="card">
                  <ScoringWeightsSliders repoId={selectedRepo.id} />
                </div>
                <div className="card">
                  <ScanScheduler repoId={selectedRepo.id} />
                </div>
                <div className="card">
                  <ExportPanel repoId={selectedRepo.id} />
                </div>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
