from app.models import EmergencyContact


class TelegramNotifier:
    def send_test(self, contact: EmergencyContact) -> tuple[bool, str]:
        if contact.telegram_chat_id:
            return True, "Тестовое уведомление отправлено."
        return False, "Telegram пока не подключен. Используйте pairing code."

    def notify_fall(self, contacts: list[EmergencyContact], user_name: str, event_time: str) -> str:
        connected = [contact for contact in contacts if contact.telegram_chat_id]
        if not contacts:
            return "no_contacts"
        if not connected:
            return "not_configured"
        if len(connected) == len(contacts):
            return "sent"
        return "partially_failed"
