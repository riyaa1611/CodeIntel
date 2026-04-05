"""add users table

Revision ID: 004
Revises: 003
Create Date: 2026-04-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("github_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(128), nullable=False),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("email", sa.String(256), nullable=True),
        sa.Column("role", sa.String(32), nullable=False, server_default="member"),
        sa.Column(
            "email_preferences",
            JSONB(),
            nullable=False,
            server_default='{"review_alerts": true, "monthly_digest": true}',
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("github_id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_github_id", "users", ["github_id"])


def downgrade() -> None:
    op.drop_index("ix_users_github_id", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
