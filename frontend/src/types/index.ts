// ── Repository ────────────────────────────────────────────────────────────────

export interface Repository {
  id: number
  github_repo_id: number | null
  full_name: string
  owner: string
  name: string
  slack_webhook_url: string | null
  created_at: string
}

export interface RepositoryCreate {
  github_repo_full_name: string
  slack_webhook_url?: string
}

// ── PR Review ─────────────────────────────────────────────────────────────────

export interface PRReviewListItem {
  id: number
  repo_id: number
  pr_number: number
  pr_title: string
  pr_author: string
  score_overall: number
  score_requirement: number
  score_security: number
  score_quality: number
  score_performance: number
  created_at: string
}

export interface PRReview extends PRReviewListItem {
  head_sha: string
  feedback_requirement: string
  feedback_security: string
  feedback_quality: string
  feedback_performance: string
  critical_issues: string[]
  warnings: string[]
  test_suggestions: string[]
  github_comment_id: number | null
  updated_at: string
}

export interface PaginatedPRReviews {
  items: PRReviewListItem[]
  total: number
  page: number
  limit: number
  pages: number
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface DimensionAverages {
  avg_overall: number
  avg_requirement: number
  avg_security: number
  avg_quality: number
  avg_performance: number
}

export interface ScoreDistribution {
  low: number
  medium: number
  high: number
}

export interface TrendDataPoint {
  date: string
  avg_score: number
  pr_count: number
}

export interface RepoStats {
  total_reviews: number
  dimension_averages: DimensionAverages
  score_distribution: ScoreDistribution
  trend_data: TrendDataPoint[]
}

export interface LeaderboardEntry {
  rank: number
  author: string
  pr_count: number
  avg_overall: number
  avg_security: number
  avg_quality: number
  avg_requirement: number
  avg_performance: number
}

export interface BenchmarkResult {
  score: number
  percentile: number
  total_reviews: number
  better_than_count: number
}

// ── Misc ──────────────────────────────────────────────────────────────────────

export type ScoreLevel = 'high' | 'medium' | 'low'

export function getScoreLevel(score: number): ScoreLevel {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

export function getScoreEmoji(score: number): string {
  if (score >= 80) return '✅'
  if (score >= 60) return '⚠️'
  return '❌'
}

export function getScoreColor(score: number): string {
  if (score >= 70) return 'text-green-600'
  if (score >= 40) return 'text-yellow-600'
  return 'text-red-600'
}

export function getScoreBg(score: number): string {
  if (score >= 70) return 'bg-green-100 text-green-800'
  if (score >= 40) return 'bg-yellow-100 text-yellow-800'
  return 'bg-red-100 text-red-800'
}

// ── Public Repo Analytics (Feature 1) ─────────────────────────────────────────

export interface ContributorInfo {
  login: string
  contributions: number
  avatar_url: string
}

export interface PublicRepoData {
  full_name: string
  description: string | null
  homepage: string | null
  topics: string[]
  stars: number
  forks: number
  open_issues: number
  watchers: number
  language: string | null
  languages: Record<string, number>
  language_percentages: Record<string, number>
  created_at: string
  pushed_at: string
  license: string | null
  default_branch: string
  contributors: ContributorInfo[]
  commits_last_30_days: number
  health_score: number
}

// ── Deep Scan (Feature 2) ──────────────────────────────────────────────────────

export interface DeepScanResult {
  id: number
  repo_id: number
  owner: string
  repo_name: string
  overall_score: number
  architecture_score: number
  security_score: number
  duplication_score: number
  documentation_score: number
  test_coverage_score: number
  critical_findings: string[]
  warnings: string[]
  positive_observations: string[]
  architecture_feedback: string
  security_feedback: string
  duplication_feedback: string
  documentation_feedback: string
  test_coverage_feedback: string
  recommended_actions: string[]
  files_analyzed: number
  created_at: string
}

export interface DeepScanHistoryItem {
  id: number
  overall_score: number
  files_analyzed: number
  created_at: string
}

export interface DeepScanTriggerResponse {
  status: string
  task_id: string
  repo_id: number
}

// ── Repository Preview (Feature 3) ────────────────────────────────────────────

export interface RepositoryPreview {
  readme_markdown: string
  live_urls: string[]
  last_updated: string
}

// ── Repo Config / Scoring Weights ─────────────────────────────────────────────

export interface ScoringWeights {
  requirement: number
  security: number
  quality: number
  performance: number
}

export interface RepoConfig {
  weights: ScoringWeights
  scan_threshold: number | null
}

// ── Scan Schedule ─────────────────────────────────────────────────────────────

export type ScanFrequency = 'daily' | 'weekly' | 'monthly'

export interface ScanSchedule {
  id: number
  repo_id: number
  frequency: ScanFrequency
  enabled: boolean
  last_run_at: string | null
  next_run_at: string
}

// ── Author Trend ──────────────────────────────────────────────────────────────

export interface AuthorTrendPoint {
  date: string
  score_overall: number
  score_requirement: number
  score_security: number
  score_quality: number
  score_performance: number
  pr_number: number
  pr_title: string
}
