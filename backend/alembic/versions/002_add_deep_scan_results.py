"""Add deep_scan_results table

Revision ID: 002
Revises: 001
Create Date: 2025-01-02 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deep_scan_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("repo_id", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("repo_name", sa.String(length=128), nullable=False),
        # Scores
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("architecture_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("security_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("duplication_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("documentation_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("test_coverage_score", sa.Float(), nullable=False, server_default="0"),
        # JSONB arrays
        sa.Column(
            "critical_findings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "positive_observations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "recommended_actions",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        # Feedback text
        sa.Column("architecture_feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("security_feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("duplication_feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("documentation_feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("test_coverage_feedback", sa.Text(), nullable=False, server_default=""),
        sa.Column("files_analyzed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repo_id"], ["repositories.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_deep_scan_results_id"), "deep_scan_results", ["id"]
    )
    op.create_index(
        op.f("ix_deep_scan_results_repo_id"), "deep_scan_results", ["repo_id"]
    )
    op.create_index(
        op.f("ix_deep_scan_results_created_at"), "deep_scan_results", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_deep_scan_results_created_at"), table_name="deep_scan_results")
    op.drop_index(op.f("ix_deep_scan_results_repo_id"), table_name="deep_scan_results")
    op.drop_index(op.f("ix_deep_scan_results_id"), table_name="deep_scan_results")
    op.drop_table("deep_scan_results")
