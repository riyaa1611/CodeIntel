from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── DeepScanResult ────────────────────────────────────────────────────────────


class Repository(Base):
    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_repo_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slack_webhook_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reviews: Mapped[list["PRReview"]] = relationship(
        "PRReview", back_populates="repository", cascade="all, delete-orphan"
    )


class PRReview(Base):
    __tablename__ = "pr_reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    pr_title: Mapped[str] = mapped_column(Text, nullable=False)
    pr_author: Mapped[str] = mapped_column(String(128), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(64), nullable=False)

    # Dimension scores
    score_overall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_requirement: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_security: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    score_performance: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Dimension feedback
    feedback_requirement: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feedback_security: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feedback_quality: Mapped[str] = mapped_column(Text, nullable=False, default="")
    feedback_performance: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Issues and suggestions
    critical_issues: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    test_suggestions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    github_comment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    repository: Mapped["Repository"] = relationship("Repository", back_populates="reviews")


class DeepScanResult(Base):
    __tablename__ = "deep_scan_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repo_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner: Mapped[str] = mapped_column(String(128), nullable=False)
    repo_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Dimension scores (0-100)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    architecture_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    security_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    duplication_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    documentation_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    test_coverage_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Findings (JSONB arrays)
    critical_findings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    positive_observations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    recommended_actions: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # Per-dimension feedback
    architecture_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    security_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    duplication_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    documentation_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")
    test_coverage_feedback: Mapped[str] = mapped_column(Text, nullable=False, default="")

    files_analyzed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )


class TaskFailure(Base):
    __tablename__ = "task_failures"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_name: Mapped[str] = mapped_column(String(256), nullable=False)
    task_args: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
