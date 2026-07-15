import hashlib
import secrets
import string
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApiError
from app.models import Device, EmergencyContact, FallIncident, UserProfile
from app.schemas.safety import FallEventCreate
from app.services.telegram import TelegramNotifier


def generate_pairing_code() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(6))


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_device(db: Session, name: str) -> tuple[Device, str]:
    secret = secrets.token_urlsafe(24)
    device = Device(
        user_id=1,
        name=name,
        device_id=f"cc-{secrets.token_hex(4)}",
        device_token_hash=hash_token(secret),
        status="active",
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device, secret


def create_fall_incident(
    db: Session,
    payload: FallEventCreate,
    device: Device | None = None,
    is_demo: bool = False,
) -> FallIncident:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    event_ts = payload.event_timestamp
    if event_ts.tzinfo is None:
        event_ts = event_ts.replace(tzinfo=timezone.utc)

    if device:
        duplicate = (
            db.query(FallIncident)
            .filter(FallIncident.device_id == device.id, FallIncident.event_timestamp == event_ts)
            .first()
        )
        if duplicate:
            raise ApiError(409, "DUPLICATE_EVENT", "Это событие уже обработано.")

        latest = (
            db.query(FallIncident)
            .filter(FallIncident.device_id == device.id)
            .order_by(FallIncident.created_at.desc())
            .first()
        )
        if latest and (now - latest.created_at.replace(tzinfo=timezone.utc)).total_seconds() < settings.device_event_cooldown_seconds:
            raise ApiError(409, "EVENT_COOLDOWN", "Событие отклонено из-за cooldown.")
        device.last_seen_at = now

    profile = db.query(UserProfile).filter(UserProfile.user_id == 1).first()
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == 1).all()
    notification_status = TelegramNotifier().notify_fall(
        contacts,
        profile.name if profile else "Азамат",
        event_ts.strftime("%H:%M"),
    )

    incident = FallIncident(
        user_id=1,
        device_id=device.id if device else None,
        event_timestamp=event_ts,
        confidence=payload.confidence,
        sensor_payload={**payload.sensor_data, "demo": is_demo},
        status="detected",
        telegram_notification_status=notification_status,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
