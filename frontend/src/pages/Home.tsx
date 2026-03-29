import { useEffect, useState } from 'react'
import { createRepo, listRepos } from '../api/client'
import type { Repository } from '../types'
import Dashboard from '../components/Dashboard'
import PRTable from '../components/PRTable'
import Leaderboard from '../components/Leaderboard'
import SlackSetup from '../components/SlackSetup'

type Tab = 'overview' | 'reviews' | 'leaderboard' | 'settings'

export default function Home() {
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
    setAddingRepo(true)
    setAddRepoError(null)
    try {
      const repo = await createRepo({
        github_repo_full_name: newRepoName.trim(),
        slack_webhook_url: newSlackUrl.trim() || undefined,
      })
      setRepos((prev) => [repo, ...prev])
      setSelectedRepo(repo)
      setNewRepoName('')
      setNewSlackUrl('')
      setShowAddRepo(false)
    } catch (err: any) {
      const msg =
        err?.response?.data?.detail ?? 'Failed to add repository'
      setAddRepoError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setAddingRepo(false)
    }
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'reviews', label: 'PR Reviews' },
    { id: 'leaderboard', label: 'Leaderboard' },
    { id: 'settings', label: 'Settings' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-14 items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-blue-600">🤖 CodeIntel</span>
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
            </div>
          </div>
        </div>
      </header>

      {/* Add repo form */}
      {showAddRepo && (
        <div className="bg-blue-50 border-b border-blue-100">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-56">
                <label className="block text-xs font-medium text-gray-600 mb-1">
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
                <label className="block text-xs font-medium text-gray-600 mb-1">
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
        {!selectedRepo ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="text-5xl mb-4">🤖</div>
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
              <h1 className="text-xl font-bold text-gray-900">
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
              <Dashboard repoId={selectedRepo.id} />
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

            {activeTab === 'settings' && (
              <div className="card max-w-2xl">
                <h2 className="mb-4 text-base font-semibold text-gray-800">
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
            )}
          </>
        )}
      </main>
    </div>
  )
}
