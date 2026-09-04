import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    bots: Mapped[list["Bot"]] = relationship(back_populates="owner")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")


class RefreshToken(Base):
    """
    Persisted so refresh tokens can be revoked (logout, logout-all-devices,
    password change) instead of relying purely on JWT expiry. jti is the
    token's unique id, embedded as a claim, so a stolen-but-revoked token
    is rejected even though it decodes successfully.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    jti: Mapped[str] = mapped_column(String, unique=True, index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class BotStatus:
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class Bot(Base):
    __tablename__ = "bots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String)
    symbol: Mapped[str] = mapped_column(String)          # e.g. "BTC/USDT"
    timeframe: Mapped[str] = mapped_column(String, default="1h")
    strategy_name: Mapped[str] = mapped_column(String)
    strategy_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    mode: Mapped[str] = mapped_column(String, default="paper")  # paper | live
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    # status distinguishes "paused" (temporarily suspended, resumes with
    # position/state intact) from "stopped" (fully torn down); is_active
    # is kept for simple filtering (status != stopped) and backward compat.
    status: Mapped[str] = mapped_column(String, default=BotStatus.STOPPED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    owner: Mapped["User"] = relationship(back_populates="bots")
    trades: Mapped[list["Trade"]] = relationship(back_populates="bot")


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bots.id"))
    symbol: Mapped[str] = mapped_column(String)
    side: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(String, default="")
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    bot: Mapped["Bot"] = relationship(back_populates="trades")


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    symbol: Mapped[str] = mapped_column(String)
    strategy_name: Mapped[str] = mapped_column(String)
    strategy_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    starting_equity: Mapped[float] = mapped_column(Float)
    ending_equity: Mapped[float] = mapped_column(Float)
    total_trades: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, default=0.0)
    equity_curve: Mapped[list] = mapped_column(JSONB, default=list)  # list of {t, equity}
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
