"""Initial schema: repositories and pr_reviews tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_repo_id", sa.BigInteger(), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slack_webhook_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("full_name"),
        sa.UniqueConstraint("github_repo_id"),
    )
    op.create_index(op.f("ix_repositories_full_name"), "repositories", ["full_name"])
    op.create_index(op.f("ix_repositories_id"), "repositories", ["id"])

    op.create_table(
        "pr_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("pr_title", sa.Text(), nullable=False),
        sa.Column("pr_author", sa.String(length=128), nullable=False),
        sa.Column("head_sha", sa.String(length=64), nullable=False),
        sa.Column("score_overall", sa.Float(), nullable=False),
        sa.Column("score_requirement", sa.Float(), nullable=False),
        sa.Column("score_security", sa.Float(), nullable=False),
        sa.Column("score_quality", sa.Float(), nullable=False),
        sa.Column("score_performance", sa.Float(), nullable=False),
        sa.Column("feedback_requirement", sa.Text(), nullable=False),
        sa.Column("feedback_security", sa.Text(), nullable=False),
        sa.Column("feedback_quality", sa.Text(), nullable=False),
        sa.Column("feedback_performance", sa.Text(), nullable=False),
        sa.Column(
            "critical_issues",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column(
            "test_suggestions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("github_comment_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"], ["repositories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pr_reviews_id"), "pr_reviews", ["id"])
    op.create_index(op.f("ix_pr_reviews_repo_id"), "pr_reviews", ["repo_id"])
    op.create_index(
        op.f("ix_pr_reviews_created_at"), "pr_reviews", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pr_reviews_created_at"), table_name="pr_reviews")
    op.drop_index(op.f("ix_pr_reviews_repo_id"), table_name="pr_reviews")
    op.drop_index(op.f("ix_pr_reviews_id"), table_name="pr_reviews")
    op.drop_table("pr_reviews")
    op.drop_index(op.f("ix_repositories_id"), table_name="repositories")
    op.drop_index(op.f("ix_repositories_full_name"), table_name="repositories")
    op.drop_table("repositories")
