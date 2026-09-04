from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "TradeSentinel"
    ENV: Literal["dev", "staging", "prod"] = "dev"
    SECRET_KEY: str = "change-me-in-production"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://tradesentinel:tradesentinel@postgres:5432/tradesentinel"

    # Redis (price cache + pub/sub for websocket fan-out)
    REDIS_URL: str = "redis://redis:6379/0"

    # Trading mode: paper never touches a real exchange; live requires API keys
    TRADING_MODE: Literal["paper", "live"] = "paper"
    EXCHANGE_NAME: str = "binance"  # any ccxt-supported exchange id
    EXCHANGE_API_KEY: str | None = None
    EXCHANGE_API_SECRET: str | None = None
    EXCHANGE_SANDBOX: bool = True  # use exchange testnet when available

    # Risk management — enforced regardless of TRADING_MODE
    MAX_POSITION_SIZE_PCT: float = 0.10       # max % of portfolio per position
    MAX_DAILY_DRAWDOWN_PCT: float = 0.05      # circuit breaker: halt trading for the day
    DEFAULT_STOP_LOSS_PCT: float = 0.03
    DEFAULT_TAKE_PROFIT_PCT: float = 0.06

    # Notifications
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    KAVEHNEGAR_API_KEY: str | None = None
    ALERT_PHONE_NUMBER: str | None = None

    # Auth
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30          # short-lived, sent on every request
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30            # long-lived, only used to mint new access tokens


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
