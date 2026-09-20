import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_backtest import router as backtest_router
from app.api.v1.routes_bots import router as bots_router
from app.api.v1.routes_market import router as market_router
from app.api.v1.routes_ws import router as ws_router
from app.api.v1.ws_manager import manager as ws_manager
from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger("tradesentinel.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ws_manager.startup()
    logger.info("TradeSentinel API started", extra={"mode": settings.TRADING_MODE, "env": settings.ENV})
    yield
    await ws_manager.shutdown()


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Tags every request with a request_id (returned in the response header
    too, so a user-reported error can be grep'd straight out of the logs)
    and logs method/path/status/duration for basic request-level observability
    without needing a separate APM tool."""
    request_id = str(uuid.uuid4())
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    response.headers["X-Request-ID"] = request_id
    logger.info(
        "Request handled",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://tredesentinel8.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(bots_router, prefix=settings.API_V1_PREFIX)
app.include_router(market_router, prefix=settings.API_V1_PREFIX)
app.include_router(backtest_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "mode": settings.TRADING_MODE}


@app.get("/metrics")
async def metrics():
    """Prometheus scrape endpoint. Not versioned under /api/v1 since it's
    infra tooling, not application API surface."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
