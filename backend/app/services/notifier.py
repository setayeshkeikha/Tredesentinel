"""
Trade notifications go out over Telegram (free, instant) and/or KavehNegar
SMS (works reliably from Iran without needing Telegram access). Both are
best-effort: a notification failure must never block or roll back a trade.
"""
import httpx

from app.core.config import settings


async def send_telegram(message: str) -> None:
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": message})
    except Exception:
        pass  # notification failures must never break the trading flow


async def send_sms(message: str) -> None:
    if not settings.KAVEHNEGAR_API_KEY or not settings.ALERT_PHONE_NUMBER:
        return
    url = f"https://api.kavenegar.com/v1/{settings.KAVEHNEGAR_API_KEY}/sms/send.json"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                url,
                data={"receptor": settings.ALERT_PHONE_NUMBER, "message": message},
            )
    except Exception:
        pass


async def notify_trade(symbol: str, side: str, amount: float, price: float, reason: str) -> None:
    message = f"[TradeSentinel] {side.upper()} {amount:.6f} {symbol} @ {price:.2f}\n{reason}"
    await send_telegram(message)
    await send_sms(message)


async def notify_halt(reason: str) -> None:
    message = f"[TradeSentinel] ⚠️ TRADING HALTED\n{reason}"
    await send_telegram(message)
    await send_sms(message)
