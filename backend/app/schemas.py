from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Repository Schemas ──────────────────────────────────────────────────────

class RepositoryCreate(BaseModel):
    github_repo_full_name: str = Field(
        ...,
        description="Full repo name in format owner/repo",
        pattern=r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$",
    )
    slack_webhook_url: str | None = Field(
        default=None, description="Optional Slack incoming webhook URL"
    )


class RepositoryUpdate(BaseModel):
    slack_webhook_url: str | None = None


class RepositoryResponse(BaseModel):
    id: int
    github_repo_id: int | None
    full_name: str
    owner: str
    name: str
    slack_webhook_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── PRReview Schemas ─────────────────────────────────────────────────────────

class PRReviewResponse(BaseModel):
    id: int
    repo_id: int
    pr_number: int
    pr_title: str
    pr_author: str
    head_sha: str
    score_overall: float
    score_requirement: float
    score_security: float
    score_quality: float
    score_performance: float
    feedback_requirement: str
    feedback_security: str
    feedback_quality: str
    feedback_performance: str
    critical_issues: list[Any]
    warnings: list[Any]
    test_suggestions: list[Any]
    github_comment_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PRReviewListItem(BaseModel):
    id: int
    repo_id: int
    pr_number: int
    pr_title: str
    pr_author: str
    score_overall: float
    score_requirement: float
    score_security: float
    score_quality: float
    score_performance: float
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedPRReviews(BaseModel):
    items: list[PRReviewListItem]
    total: int
    page: int
    limit: int
    pages: int


# ── Analytics Schemas ────────────────────────────────────────────────────────

class DimensionAverages(BaseModel):
    avg_overall: float
    avg_requirement: float
    avg_security: float
    avg_quality: float
    avg_performance: float


class ScoreDistribution(BaseModel):
    low: int = Field(description="PRs with score 0-40")
    medium: int = Field(description="PRs with score 41-70")
    high: int = Field(description="PRs with score 71-100")


class TrendDataPoint(BaseModel):
    date: str
    avg_score: float
    pr_count: int


class RepoStats(BaseModel):
    total_reviews: int
    dimension_averages: DimensionAverages
    score_distribution: ScoreDistribution
    trend_data: list[TrendDataPoint]


class LeaderboardEntry(BaseModel):
    rank: int
    author: str
    pr_count: int
    avg_overall: float
    avg_security: float
    avg_quality: float
    avg_requirement: float
    avg_performance: float


class BenchmarkResult(BaseModel):
    score: float
    percentile: float
    total_reviews: int
    better_than_count: int


class AuthorTrendPoint(BaseModel):
    date: str
    score_overall: float
    score_requirement: float
    score_security: float
    score_quality: float
    score_performance: float
    pr_number: int
    pr_title: str


# ── AI Review Output Schema ──────────────────────────────────────────────────

class AIReviewOutput(BaseModel):
    score_overall: float
    score_requirement: float
    score_security: float
    score_quality: float
    score_performance: float
    feedback_requirement: str
    feedback_security: str
    feedback_quality: str
    feedback_performance: str
    critical_issues: list[str]
    warnings: list[str]
    test_suggestions: list[str]

    @field_validator(
        "score_overall",
        "score_requirement",
        "score_security",
        "score_quality",
        "score_performance",
    )
    @classmethod
    def clamp_score(cls, v: float) -> float:
        return max(0.0, min(100.0, float(v)))


# ── Webhook Schemas ──────────────────────────────────────────────────────────

class WebhookResponse(BaseModel):
    status: str
    message: str


# ── Slack Setup Schema ───────────────────────────────────────────────────────

class SlackWebhookUpdate(BaseModel):
    slack_webhook_url: str = Field(..., description="Slack incoming webhook URL")


# ── Repo Config / Scoring Weights Schemas ────────────────────────────────────

class ScoringWeights(BaseModel):
    requirement: int = Field(default=30, ge=5, le=80)
    security: int = Field(default=30, ge=5, le=80)
    quality: int = Field(default=20, ge=5, le=80)
    performance: int = Field(default=20, ge=5, le=80)

    @model_validator(mode="after")
    def weights_sum_to_100(self) -> "ScoringWeights":
        total = self.requirement + self.security + self.quality + self.performance
        if total != 100:
            raise ValueError(f"Weights must sum to 100, got {total}")
        return self


class RepoConfigResponse(BaseModel):
    weights: ScoringWeights
    scan_threshold: int | None = None


class RepoConfigUpdate(BaseModel):
    weights: ScoringWeights
    scan_threshold: int | None = Field(default=None, ge=0, le=100, description="Auto-trigger deep scan when PR score falls below this value (None = disabled)")


# ── Scan Schedule Schemas ────────────────────────────────────────────────────

class ScanScheduleResponse(BaseModel):
    id: int
    repo_id: int
    frequency: str
    enabled: bool
    last_run_at: datetime | None
    next_run_at: datetime

    model_config = {"from_attributes": True}


class ScanScheduleUpdate(BaseModel):
    frequency: str = Field(..., pattern=r"^(daily|weekly|monthly)$")
    enabled: bool = True
