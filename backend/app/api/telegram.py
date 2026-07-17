from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.core.errors import ApiError
from app.schemas.common import MessageResponse
from app.services import telegram_bot

router = APIRouter(tags=["telegram"])


@router.post("/api/telegram/webhook/{secret}", response_model=MessageResponse, include_in_schema=False)
async def telegram_webhook(secret: str, update: dict):
    settings = get_settings()
    if not settings.telegram_bot_token or not settings.telegram_webhook_secret:
        raise ApiError(404, "TELEGRAM_NOT_CONFIGURED", "Telegram webhook не настроен.")
    if secret != settings.telegram_webhook_secret:
        raise ApiError(403, "INVALID_TELEGRAM_WEBHOOK", "Неверный Telegram webhook.")

    chat_id, reply_text = telegram_bot.handle_update(update)
    if chat_id and reply_text:
        await telegram_bot.reply(settings.telegram_bot_token, chat_id, reply_text)

    return MessageResponse(ok=True, message="ok")
