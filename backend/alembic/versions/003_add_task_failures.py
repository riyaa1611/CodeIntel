"""add task_failures table

Revision ID: 003
Revises: 002
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_failures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_name", sa.String(256), nullable=False),
        sa.Column("task_args", JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("traceback_text", sa.Text(), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_task_failures_id", "task_failures", ["id"])
    op.create_index("ix_task_failures_failed_at", "task_failures", ["failed_at"])


def downgrade() -> None:
    op.drop_index("ix_task_failures_failed_at", table_name="task_failures")
    op.drop_index("ix_task_failures_id", table_name="task_failures")
    op.drop_table("task_failures")
