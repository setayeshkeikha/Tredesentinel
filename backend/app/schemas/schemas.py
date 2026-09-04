from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StrategyParamsBase(BaseModel):
    strategy_name: str = Field(..., examples=["rsi", "macd", "grid"])
    strategy_params: dict = Field(default_factory=dict)


class BotCreate(StrategyParamsBase):
    name: str
    symbol: str = Field(..., examples=["BTC/USDT"])
    timeframe: str = "1h"
    mode: str = "paper"


class BotOut(BotCreate):
    id: str
    is_active: bool
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class BacktestRequest(StrategyParamsBase):
    symbol: str
    timeframe: str = "1h"
    candle_limit: int = 500
    starting_equity: float = 10_000.0


class BacktestTradeOut(BaseModel):
    timestamp: str
    side: str
    price: float
    amount: float
    reason: str
    pnl: float | None = None


class BacktestResponse(BaseModel):
    starting_equity: float
    ending_equity: float
    total_trades: int
    win_rate: float
    max_drawdown_pct: float
    equity_curve: list[dict]
    trades: list[BacktestTradeOut]


class TickerOut(BaseModel):
    symbol: str
    price: float


class PortfolioOut(BaseModel):
    quote_asset: str
    total_value: float
    mode: str


class TradeOut(BaseModel):
    id: str
    symbol: str
    side: str
    amount: float
    price: float
    fee: float
    reason: str
    pnl: float | None
    executed_at: datetime

    class Config:
        from_attributes = True
