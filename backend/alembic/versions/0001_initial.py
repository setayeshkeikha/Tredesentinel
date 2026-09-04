"""initial schema: users, bots, trades, backtest_results

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "bots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("timeframe", sa.String(), nullable=False, server_default="1h"),
        sa.Column("strategy_name", sa.String(), nullable=False),
        sa.Column("strategy_params", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("mode", sa.String(), nullable=False, server_default="paper"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_bots_owner_id", "bots", ["owner_id"])
    op.create_index("ix_bots_is_active", "bots", ["is_active"])

    op.create_table(
        "trades",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bot_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bots.id"), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("fee", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(), nullable=False, server_default=""),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
    )
    # Composite index matching the strategy runner's most common query:
    # "most recent trade for this bot+symbol" (see _get_open_position).
    op.create_index("ix_trades_bot_symbol_executed_at", "trades", ["bot_id", "symbol", "executed_at"])

    op.create_table(
        "backtest_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("strategy_name", sa.String(), nullable=False),
        sa.Column("strategy_params", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("starting_equity", sa.Float(), nullable=False),
        sa.Column("ending_equity", sa.Float(), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("max_drawdown_pct", sa.Float(), nullable=False, server_default="0"),
        sa.Column("equity_curve", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_backtest_results_owner_id", "backtest_results", ["owner_id"])


def downgrade() -> None:
    op.drop_table("backtest_results")
    op.drop_index("ix_trades_bot_symbol_executed_at", table_name="trades")
    op.drop_table("trades")
    op.drop_index("ix_bots_is_active", table_name="bots")
    op.drop_index("ix_bots_owner_id", table_name="bots")
    op.drop_table("bots")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
