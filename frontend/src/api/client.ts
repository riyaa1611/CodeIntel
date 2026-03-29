import axios from 'axios'
import type {
  BenchmarkResult,
  LeaderboardEntry,
  PaginatedPRReviews,
  PRReview,
  Repository,
  RepositoryCreate,
  RepoStats,
} from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Repositories ──────────────────────────────────────────────────────────────

export async function listRepos(): Promise<Repository[]> {
  const { data } = await api.get<Repository[]>('/api/repos')
  return data
}

export async function createRepo(body: RepositoryCreate): Promise<Repository> {
  const { data } = await api.post<Repository>('/api/repos', body)
  return data
}

export async function updateSlackWebhook(
  repoId: number,
  slackWebhookUrl: string
): Promise<Repository> {
  const { data } = await api.patch<Repository>(`/api/repos/${repoId}/slack`, {
    slack_webhook_url: slackWebhookUrl,
  })
  return data
}

// ── Reviews ───────────────────────────────────────────────────────────────────

export async function listReviews(
  repoId: number,
  params: {
    page?: number
    limit?: number
    min_score?: number
    max_score?: number
  } = {}
): Promise<PaginatedPRReviews> {
  const { data } = await api.get<PaginatedPRReviews>(
    `/api/repos/${repoId}/reviews`,
    { params }
  )
  return data
}

export async function getReview(
  repoId: number,
  reviewId: number
): Promise<PRReview> {
  const { data } = await api.get<PRReview>(
    `/api/repos/${repoId}/reviews/${reviewId}`
  )
  return data
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function getRepoStats(repoId: number): Promise<RepoStats> {
  const { data } = await api.get<RepoStats>(`/api/repos/${repoId}/stats`)
  return data
}

export async function getLeaderboard(
  repoId: number
): Promise<LeaderboardEntry[]> {
  const { data } = await api.get<LeaderboardEntry[]>(
    `/api/repos/${repoId}/leaderboard`
  )
  return data
}

export async function getBenchmark(
  repoId: number,
  score: number
): Promise<BenchmarkResult> {
  const { data } = await api.get<BenchmarkResult>(
    `/api/repos/${repoId}/benchmark/${score}`
  )
  return data
}
