"""Telegram Bot API client.

This module previously returned hardcoded success strings without contacting
Telegram. Everything here now performs a real HTTP call and reports what
actually happened — an alert system that lies about delivery is worse than none,
because the family stops watching for the alert that never comes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import httpx

from app.core.config import get_settings
from app.models import EmergencyContact

API_BASE = "https://api.telegram.org"
TIMEOUT = httpx.Timeout(10.0)


class TelegramNotifier:
    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def configured(self) -> bool:
        return bool(self._settings.telegram_bot_token)

    def _url(self, method: str) -> str:
        return f"{API_BASE}/bot{self._settings.telegram_bot_token}/{method}"

    def send_message(self, chat_id: str, text: str) -> tuple[bool, str]:
        if not self.configured:
            return False, "TELEGRAM_BOT_TOKEN не задан на сервере."
        try:
            response = httpx.post(
                self._url("sendMessage"),
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=TIMEOUT,
            )
            body = response.json()
        except httpx.HTTPError as exc:
            return False, f"Сеть недоступна: {exc}"
        except ValueError:
            return False, "Telegram вернул неожиданный ответ."

        if response.status_code == 200 and body.get("ok"):
            return True, "Сообщение доставлено."
        return False, str(body.get("description", f"HTTP {response.status_code}"))

    # ---------------------------------------------------------------- public
    def send_test(self, contact: EmergencyContact) -> tuple[bool, str]:
        if not contact.telegram_chat_id:
            username = self._settings.telegram_bot_username
            return False, (
                f"Telegram не подключен. Попросите контакт открыть @{username} "
                f"и отправить: /start {contact.pairing_code}"
            )
        return self.send_message(
            contact.telegram_chat_id,
            "✅ <b>Instant Rescue</b>\n\nЭто тестовое сообщение. "
            "Уведомления о падении будут приходить сюда.",
        )

    def notify_fall(
        self,
        contacts: list[EmergencyContact],
        user_name: str,
        event_time: datetime,
        confidence: Optional[float] = None,
        hr_context: Optional[dict] = None,
    ) -> tuple[str, list[dict]]:
        """Alert every paired contact. Returns (status, per-contact detail)."""
        if not contacts:
            return "no_contacts", []

        paired = [c for c in contacts if c.telegram_chat_id]
        if not paired:
            return "not_configured", [
                {
                    "contact_id": c.id,
                    "contact_name": c.name,
                    "ok": False,
                    "detail": "Контакт не завершил подключение Telegram.",
                }
                for c in contacts
            ]

        text = self._fall_message(user_name, event_time, confidence, hr_context)
        detail = []
        for contact in paired:
            ok, message = self.send_message(contact.telegram_chat_id, text)
            detail.append(
                {"contact_id": contact.id, "contact_name": contact.name, "ok": ok, "detail": message}
            )

        delivered = sum(1 for item in detail if item["ok"])
        if delivered == 0:
            return "failed", detail
        if delivered < len(detail):
            return "partially_failed", detail
        return "sent", detail

    @staticmethod
    def _fall_message(
        user_name: str,
        event_time: datetime,
        confidence: Optional[float],
        hr_context: Optional[dict],
    ) -> str:
        lines = [
            "🚨 <b>Возможное падение</b>",
            "",
            f"<b>Кто:</b> {user_name}",
            f"<b>Когда:</b> {event_time.strftime('%d.%m.%Y %H:%M')}",
        ]
        if confidence is not None:
            lines.append(f"<b>Уверенность датчика:</b> {int(confidence * 100)}%")

        if hr_context:
            bpm = hr_context.get("bpm")
            severity = hr_context.get("severity")
            if bpm:
                lines.append(f"<b>Пульс на момент события:</b> {bpm:.0f} уд/мин")
            if severity and severity != "normal":
                lines.append(f"<b>Оценка ритма:</b> {severity}")

        lines += [
            "",
            "Пожалуйста, свяжитесь с человеком прямо сейчас.",
            "Если он не отвечает — вызовите скорую помощь (103).",
            "",
            "<i>Это сигнал датчика, а не медицинский диагноз. Решение принимаете вы.</i>",
        ]
        return "\n".join(lines)
