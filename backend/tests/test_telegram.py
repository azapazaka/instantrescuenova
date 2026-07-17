"""Notification honesty.

The previous implementation returned "sent" without contacting Telegram. These
tests exist so that regression cannot come back quietly.
"""

from datetime import datetime, timezone

from app.services.telegram import TelegramNotifier


class _Contact:
    def __init__(self, chat_id=None, name="Мама"):
        self.id = 1
        self.name = name
        self.relationship = "Дочь"
        self.telegram_chat_id = chat_id
        self.pairing_code = "ABC123"


def test_no_contacts_reports_no_contacts():
    status, detail = TelegramNotifier().notify_fall([], "Азамат", datetime.now(timezone.utc))
    assert status == "no_contacts"
    assert detail == []


def test_unpaired_contact_is_not_reported_as_sent():
    status, detail = TelegramNotifier().notify_fall(
        [_Contact(chat_id=None)], "Азамат", datetime.now(timezone.utc)
    )
    assert status == "not_configured"
    assert detail[0]["ok"] is False


def test_send_without_token_fails_loudly():
    ok, message = TelegramNotifier().send_message("123", "test")
    assert ok is False
    assert "TELEGRAM_BOT_TOKEN" in message


def test_test_message_to_unpaired_contact_returns_pairing_instructions():
    ok, message = TelegramNotifier().send_test(_Contact(chat_id=None))
    assert ok is False
    assert "/start ABC123" in message


def test_fall_message_contains_the_essentials():
    message = TelegramNotifier._fall_message(
        "Азамат",
        datetime(2026, 7, 17, 14, 30, tzinfo=timezone.utc),
        0.91,
        {"bpm": 148.0, "severity": "high"},
    )
    assert "Азамат" in message
    assert "17.07.2026 14:30" in message
    assert "91%" in message
    assert "148" in message
    assert "103" in message  # ambulance number
    assert "не медицинский диагноз" in message


def test_fall_message_omits_hr_when_unknown():
    message = TelegramNotifier._fall_message(
        "Азамат", datetime.now(timezone.utc), None, None
    )
    assert "Пульс на момент события" not in message
