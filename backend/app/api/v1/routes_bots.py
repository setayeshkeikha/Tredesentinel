import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.models import Bot, BotStatus, Trade, User
from app.schemas.schemas import BotCreate, BotOut, TradeOut
from app.services.strategies.registry import STRATEGY_REGISTRY

router = APIRouter(prefix="/bots", tags=["bots"])


def _to_bot_out(bot: Bot) -> BotOut:
    return BotOut(
        id=str(bot.id),
        name=bot.name,
        symbol=bot.symbol,
        timeframe=bot.timeframe,
        strategy_name=bot.strategy_name,
        strategy_params=bot.strategy_params or {},
        mode=bot.mode,
        is_active=bot.is_active,
        status=bot.status,
        created_at=bot.created_at,
    )


@router.post("", response_model=BotOut, status_code=201)
async def create_bot(
    payload: BotCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if payload.strategy_name not in STRATEGY_REGISTRY:
        available = ", ".join(STRATEGY_REGISTRY.keys())
        raise HTTPException(status_code=400, detail=f"Unknown strategy. Available: {available}")

    bot = Bot(
        owner_id=user.id,
        name=payload.name,
        symbol=payload.symbol,
        timeframe=payload.timeframe,
        strategy_name=payload.strategy_name,
        strategy_params=payload.strategy_params,
        mode=payload.mode,
        is_active=False,
        status=BotStatus.STOPPED,
    )
    db.add(bot)
    await db.commit()
    await db.refresh(bot)
    return _to_bot_out(bot)


@router.get("", response_model=list[BotOut])
async def list_bots(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Bot).where(Bot.owner_id == user.id).order_by(Bot.created_at.desc()))
    return [_to_bot_out(b) for b in result.scalars().all()]


async def _get_owned_bot(bot_id: str, db: AsyncSession, user: User) -> Bot:
    try:
        parsed_id = uuid.UUID(bot_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Bot not found")

    result = await db.execute(select(Bot).where(Bot.id == parsed_id, Bot.owner_id == user.id))
    bot = result.scalar_one_or_none()
    if bot is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot


@router.get("/{bot_id}", response_model=BotOut)
async def get_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bot = await _get_owned_bot(bot_id, db, user)
    return _to_bot_out(bot)


@router.post("/{bot_id}/start", response_model=BotOut)
async def start_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Starts a stopped or resumes a paused bot. Starting from STOPPED begins
    a fresh run (no prior open position assumed); resuming from PAUSED keeps
    whatever position/state the in-memory strategy runner already holds for
    this bot_id, since pausing never tears that state down."""
    bot = await _get_owned_bot(bot_id, db, user)
    bot.is_active = True
    bot.status = BotStatus.RUNNING
    await db.commit()
    await db.refresh(bot)
    return _to_bot_out(bot)


@router.post("/{bot_id}/pause", response_model=BotOut)
async def pause_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Temporarily suspends scheduling new ticks without closing any open
    position or discarding strategy state — use this for a deliberate,
    resumable break (e.g. going offline briefly), as opposed to /stop which
    is a full teardown."""
    bot = await _get_owned_bot(bot_id, db, user)
    if bot.status != BotStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Only a running bot can be paused")
    bot.is_active = False
    bot.status = BotStatus.PAUSED
    await db.commit()
    await db.refresh(bot)
    return _to_bot_out(bot)


@router.post("/{bot_id}/stop", response_model=BotOut)
async def stop_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bot = await _get_owned_bot(bot_id, db, user)
    bot.is_active = False
    bot.status = BotStatus.STOPPED
    await db.commit()
    await db.refresh(bot)
    return _to_bot_out(bot)


@router.delete("/{bot_id}", status_code=204)
async def delete_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bot = await _get_owned_bot(bot_id, db, user)
    await db.delete(bot)
    await db.commit()


@router.get("/{bot_id}/trades", response_model=list[TradeOut])
async def list_bot_trades(
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    bot = await _get_owned_bot(bot_id, db, user)
    result = await db.execute(
        select(Trade).where(Trade.bot_id == bot.id).order_by(Trade.executed_at.desc()).limit(200)
    )
    return [
        TradeOut(
            id=str(t.id),
            symbol=t.symbol,
            side=t.side,
            amount=t.amount,
            price=t.price,
            fee=t.fee,
            reason=t.reason,
            pnl=t.pnl,
            executed_at=t.executed_at,
        )
        for t in result.scalars().all()
    ]
