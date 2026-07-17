"""Telegram pairing worker.

Long polling rather than a webhook, deliberately: a webhook needs a public
HTTPS URL, which means a tunnel that expires mid-demo. getUpdates works from a
laptop on conference wifi with no setup, which is exactly the environment this
has to survive.

Flow: the app shows the relative a code (`/start ABC123`). They send it to the
bot. We match the code to an EmergencyContact, store their chat_id, and from
then on fall alerts reach them.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Optional

import httpx

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models import EmergencyContact
from app.services.telegram import API_BASE

POLL_TIMEOUT = 25  # seconds Telegram holds the connection open
_task: Optional[asyncio.Task] = None


def _handle_start(code: str, chat_id: str, username: Optional[str]) -> str:
    """Pair a chat with a contact. Returns the reply to send back."""
    db = SessionLocal()
    try:
        contact = (
            db.query(EmergencyContact)
            .filter(EmergencyContact.pairing_code == code.upper())
            .first()
        )
        if not contact:
            return (
                "❌ Код не найден.\n\nПроверьте код в приложении Instant Rescue "
                "и отправьте его ещё раз в формате: /start ВАШКОД"
            )

        contact.telegram_chat_id = str(chat_id)
        contact.status = "connected"
        if username and not contact.telegram_username:
            contact.telegram_username = f"@{username}"
        db.add(contact)
        db.commit()

        return (
            f"✅ <b>Подключено</b>\n\nВы указаны как экстренный контакт "
            f"({contact.relationship}).\n\n"
            "Если система зафиксирует падение, вы получите сообщение сюда — "
            "с временем события и показателями пульса.\n\n"
            "<i>Instant Rescue не ставит диагноз. Решение всегда за вами.</i>"
        )
    finally:
        db.close()


async def _reply(client: httpx.AsyncClient, token: str, chat_id: str, text: str) -> None:
    with contextlib.suppress(httpx.HTTPError):
        await client.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )


async def reply(token: str, chat_id: str, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        await _reply(client, token, chat_id, text)


def handle_update(update: dict) -> tuple[Optional[str], Optional[str]]:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    if not text.startswith("/start"):
        return None, None

    chat_id = str(chat.get("id"))
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return (
            chat_id,
            "Здравствуйте! Отправьте код из приложения Instant Rescue "
            "в формате: /start ВАШКОД",
        )

    return chat_id, _handle_start(parts[1].strip(), chat_id, chat.get("username"))


async def _poll_loop(token: str) -> None:
    offset = 0
    async with httpx.AsyncClient(timeout=POLL_TIMEOUT + 10) as client:
        print("[telegram] pairing worker started")
        while True:
            try:
                response = await client.get(
                    f"{API_BASE}/bot{token}/getUpdates",
                    params={"offset": offset, "timeout": POLL_TIMEOUT},
                )
                payload = response.json()
                if not payload.get("ok"):
                    print(f"[telegram] getUpdates error: {payload.get('description')}")
                    await asyncio.sleep(5)
                    continue

                for update in payload.get("result", []):
                    offset = update["update_id"] + 1
                    # DB work is sync; keep it off the event loop.
                    chat_id, reply_text = await asyncio.to_thread(handle_update, update)
                    if chat_id and reply_text:
                        await _reply(client, token, chat_id, reply_text)

            except asyncio.CancelledError:
                print("[telegram] pairing worker stopped")
                raise
            except Exception as exc:
                # Never let a transient failure kill the worker for the session.
                print(f"[telegram] poll error: {exc}")
                await asyncio.sleep(5)


def start(loop_factory=asyncio.get_event_loop) -> None:
    global _task
    settings = get_settings()
    if not settings.telegram_polling_enabled or not settings.telegram_bot_token:
        print("[telegram] pairing worker disabled (no token or polling off)")
        return
    if _task and not _task.done():
        return
    _task = asyncio.create_task(_poll_loop(settings.telegram_bot_token))


async def stop() -> None:
    global _task
    if _task and not _task.done():
        _task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _task
    _task = None
