import axios from 'axios'
import type {
  AuthorTrendPoint,
  BenchmarkResult,
  DeepScanHistoryItem,
  DeepScanResult,
  DeepScanTriggerResponse,
  LeaderboardEntry,
  PaginatedPRReviews,
  PRReview,
  PublicRepoData,
  RepoConfig,
  Repository,
  RepositoryCreate,
  RepositoryPreview,
  RepoStats,
  ScanFrequency,
  ScanSchedule,
  ScoringWeights,
} from '../types'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

export const apiClient = api

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

// ── Public Repo Analytics (Feature 1) ────────────────────────────────────────

export async function getPublicRepo(owner: string, repo: string): Promise<PublicRepoData> {
  const { data } = await api.get<PublicRepoData>(`/api/public/repo/${owner}/${repo}`)
  return data
}

// ── Deep Scan (Feature 2) ─────────────────────────────────────────────────────

export async function triggerDeepScan(repoId: number): Promise<DeepScanTriggerResponse> {
  const { data } = await api.post<DeepScanTriggerResponse>(
    `/api/repos/${repoId}/deep-scan`
  )
  return data
}

export async function getLatestDeepScan(repoId: number): Promise<DeepScanResult> {
  const { data } = await api.get<DeepScanResult>(
    `/api/repos/${repoId}/deep-scan/latest`
  )
  return data
}

export async function getDeepScanHistory(repoId: number): Promise<DeepScanHistoryItem[]> {
  const { data } = await api.get<DeepScanHistoryItem[]>(
    `/api/repos/${repoId}/deep-scan/history`
  )
  return data
}

// ── Repository Preview (Feature 3) ───────────────────────────────────────────

export async function getRepoPreview(repoId: number): Promise<RepositoryPreview> {
  const { data } = await api.get<RepositoryPreview>(`/api/repos/${repoId}/preview`)
  return data
}

// ── PR Diff ───────────────────────────────────────────────────────────────────

export async function getReviewDiff(repoId: number, reviewId: number): Promise<string> {
  const { data } = await api.get<string>(
    `/api/repos/${repoId}/reviews/${reviewId}/diff`,
    { responseType: 'text' }
  )
  return data
}

// ── Author Trend ──────────────────────────────────────────────────────────────

export async function getAuthorTrend(repoId: number, author: string): Promise<AuthorTrendPoint[]> {
  const { data } = await api.get<AuthorTrendPoint[]>(
    `/api/repos/${repoId}/authors/${encodeURIComponent(author)}/trend`
  )
  return data
}

// ── Repo Config ───────────────────────────────────────────────────────────────

export async function getRepoConfig(repoId: number): Promise<RepoConfig> {
  const { data } = await api.get<RepoConfig>(`/api/repos/${repoId}/config`)
  return data
}

export async function updateRepoConfig(
  repoId: number,
  weights: ScoringWeights,
  scanThreshold: number | null = null
): Promise<RepoConfig> {
  const { data } = await api.patch<RepoConfig>(`/api/repos/${repoId}/config`, {
    weights,
    scan_threshold: scanThreshold,
  })
  return data
}

// ── Scan Schedule ─────────────────────────────────────────────────────────────

export async function getScanSchedule(repoId: number): Promise<ScanSchedule | null> {
  try {
    const { data } = await api.get<ScanSchedule>(`/api/repos/${repoId}/scan-schedule`)
    return data
  } catch (err: any) {
    if (err?.response?.status === 404) return null
    throw err
  }
}

export async function upsertScanSchedule(
  repoId: number,
  frequency: ScanFrequency,
  enabled: boolean
): Promise<ScanSchedule> {
  const { data } = await api.put<ScanSchedule>(`/api/repos/${repoId}/scan-schedule`, {
    frequency,
    enabled,
  })
  return data
}

// ── Auth interceptor ──────────────────────────────────────────────────────────

apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
