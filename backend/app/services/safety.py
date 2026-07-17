from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Optional

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


def create_device(db: Session, user_id: str, name: str) -> tuple[Device, str]:
    secret = secrets.token_urlsafe(24)
    device = Device(
        user_id=user_id,
        name=name,
        device_id=f"ir-{secrets.token_hex(4)}",
        device_token_hash=hash_token(secret),
        status="active",
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    # The plaintext secret is returned exactly once; only its hash is stored.
    return device, secret


def _hr_context(db: Session, user_id: str) -> Optional[dict]:
    """Pulse around the moment of the fall, for the alert message.

    A relative deciding whether to call an ambulance is helped far more by
    "pulse 148, rhythm flagged" than by "fall detected".
    """
    from app.services.heart_rate import latest_anomaly, latest_reading

    reading = latest_reading(db, user_id)
    anomaly = latest_anomaly(db, user_id)
    if not reading and not anomaly:
        return None

    context: dict = {}
    if reading:
        context["bpm"] = reading.bpm
        context["measured_at"] = reading.measured_at.isoformat()
    if anomaly:
        context["severity"] = anomaly.severity
        context["anomaly_score"] = anomaly.anomaly_score
    return context


def create_fall_incident(
    db: Session,
    user_id: str,
    payload: FallEventCreate,
    device: Optional[Device] = None,
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
        if latest:
            created = latest.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if (now - created).total_seconds() < settings.device_event_cooldown_seconds:
                raise ApiError(409, "EVENT_COOLDOWN", "Событие отклонено из-за cooldown.")
        device.last_seen_at = now

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    contacts = db.query(EmergencyContact).filter(EmergencyContact.user_id == user_id).all()
    hr_context = _hr_context(db, user_id)

    status, detail = TelegramNotifier().notify_fall(
        contacts,
        (profile.name if profile and profile.name else "Пользователь"),
        event_ts,
        payload.confidence,
        hr_context,
    )

    incident = FallIncident(
        user_id=user_id,
        device_id=device.id if device else None,
        event_timestamp=event_ts,
        confidence=payload.confidence,
        sensor_payload={**payload.sensor_data, "demo": is_demo},
        status="detected",
        telegram_notification_status=status,
        notification_detail=detail,
        hr_context=hr_context,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident
