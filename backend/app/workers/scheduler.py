"""
Standalone process (run as the `worker` service in docker-compose) that
ticks each active bot on a schedule via APScheduler.

Unlike a static config list, this scheduler polls the Bot table every
RECONCILE_INTERVAL_SECONDS and adds/removes jobs to match which bots are
currently marked is_active=True. Starting or stopping a bot through the
API (see routes_bots.py) takes effect here within one reconcile cycle,
without restarting the worker process.
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from app.core.logging_config import configure_logging
from app.core.metrics import active_bots as active_bots_gauge
from app.db.session import SessionLocal
from app.models.models import Bot
from app.workers.strategy_runner import run_bot_tick

configure_logging()
logger = logging.getLogger("tradesentinel.scheduler")

RECONCILE_INTERVAL_SECONDS = 15
DEFAULT_TICK_INTERVAL_SECONDS = 60


async def _fetch_active_bots() -> list[Bot]:
    async with SessionLocal() as db:
        result = await db.execute(select(Bot).where(Bot.is_active.is_(True)))
        return list(result.scalars().all())


async def reconcile(scheduler: AsyncIOScheduler) -> None:
    try:
        active_bots = await _fetch_active_bots()
    except Exception:
        logger.exception("Failed to load active bots from database; leaving existing jobs untouched")
        return

    active_ids = {str(bot.id) for bot in active_bots}
    scheduled_ids = {job.id for job in scheduler.get_jobs() if job.id != "reconcile"}

    for job_id in scheduled_ids - active_ids:
        scheduler.remove_job(job_id)
        logger.info("Stopped bot (no longer active)", extra={"bot_id": job_id})

    for bot in active_bots:
        job_id = str(bot.id)
        if job_id in scheduled_ids:
            continue
        scheduler.add_job(
            run_bot_tick,
            trigger=IntervalTrigger(seconds=DEFAULT_TICK_INTERVAL_SECONDS),
            kwargs={
                "bot_id": job_id,
                "symbol": bot.symbol,
                "timeframe": bot.timeframe,
                "strategy_name": bot.strategy_name,
                "strategy_params": bot.strategy_params or {},
            },
            id=job_id,
            replace_existing=True,
        )
        logger.info("Started bot", extra={"bot_id": job_id, "symbol": bot.symbol, "strategy": bot.strategy_name})

    active_bots_gauge.set(len(active_ids))


async def main() -> None:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        reconcile,
        trigger=IntervalTrigger(seconds=RECONCILE_INTERVAL_SECONDS),
        kwargs={"scheduler": scheduler},
        id="reconcile",
    )
    scheduler.start()
    await reconcile(scheduler)  # run once immediately instead of waiting for the first interval

    logger.info("Scheduler started, reconciling every %ss", RECONCILE_INTERVAL_SECONDS)
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
