"""add refresh_tokens table and bots.status column

Revision ID: 0002_refresh_tokens_bot_status
Revises: 0001_initial
Create Date: 2026-07-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_refresh_tokens_bot_status"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("jti", sa.String(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # status carries strictly more information than the pre-existing
    # is_active boolean (adds a distinct PAUSED state), so it's backfilled
    # from is_active for any rows that predate this migration rather than
    # defaulting everyone to 'stopped'.
    op.add_column(
        "bots",
        sa.Column("status", sa.String(), nullable=False, server_default="stopped"),
    )
    op.execute("UPDATE bots SET status = 'running' WHERE is_active = true")


def downgrade() -> None:
    op.drop_column("bots", "status")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
