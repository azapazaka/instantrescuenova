from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import Device, EmergencyContact, FallIncident
from app.schemas.common import MessageResponse
from app.schemas.safety import (
    DeviceCreate,
    DeviceCreated,
    DeviceRead,
    EmergencyContactCreate,
    EmergencyContactRead,
    FallEventCreate,
    FallIncidentRead,
)
from app.services.safety import create_device, create_fall_incident, generate_pairing_code, hash_token
from app.services.telegram import TelegramNotifier

router = APIRouter(tags=["safety"])


@router.get("/api/emergency-contacts", response_model=list[EmergencyContactRead])
def list_contacts(db: Session = Depends(get_db)):
    return db.query(EmergencyContact).filter(EmergencyContact.user_id == 1).order_by(EmergencyContact.created_at.desc()).all()


@router.post("/api/emergency-contacts", response_model=EmergencyContactRead)
def add_contact(payload: EmergencyContactCreate, db: Session = Depends(get_db)):
    contact = EmergencyContact(
        user_id=1,
        name=payload.name,
        relationship=payload.relationship,
        pairing_code=generate_pairing_code(),
        status="waiting",
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.delete("/api/emergency-contacts/{contact_id}", response_model=MessageResponse)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == 1).first()
    if not contact:
        raise ApiError(404, "CONTACT_NOT_FOUND", "Контакт не найден.")
    db.delete(contact)
    db.commit()
    return MessageResponse(ok=True, message="Контакт удален.")


@router.post("/api/emergency-contacts/{contact_id}/test", response_model=MessageResponse)
def test_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == 1).first()
    if not contact:
        raise ApiError(404, "CONTACT_NOT_FOUND", "Контакт не найден.")
    ok, message = TelegramNotifier().send_test(contact)
    return MessageResponse(ok=ok, message=message)


@router.post("/api/emergency-contacts/{contact_id}/regenerate-pairing", response_model=EmergencyContactRead)
def regenerate_pairing(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(EmergencyContact).filter(EmergencyContact.id == contact_id, EmergencyContact.user_id == 1).first()
    if not contact:
        raise ApiError(404, "CONTACT_NOT_FOUND", "Контакт не найден.")
    contact.pairing_code = generate_pairing_code()
    contact.status = "waiting"
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return contact


@router.get("/api/devices", response_model=list[DeviceRead])
def list_devices(db: Session = Depends(get_db)):
    return db.query(Device).filter(Device.user_id == 1).order_by(Device.created_at.desc()).all()


@router.post("/api/devices", response_model=DeviceCreated)
def add_device(payload: DeviceCreate, db: Session = Depends(get_db)):
    device, secret = create_device(db, payload.name)
    return {**DeviceRead.model_validate(device).model_dump(), "device_secret": secret}


@router.post("/api/devices/{device_id}/fall-events", response_model=FallIncidentRead)
def device_fall_event(
    device_id: str,
    payload: FallEventCreate,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    device = db.query(Device).filter(Device.device_id == device_id, Device.user_id == 1).first()
    if not device:
        raise ApiError(404, "DEVICE_NOT_FOUND", "Устройство не найдено.")
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if hash_token(token) != device.device_token_hash:
        raise ApiError(401, "INVALID_DEVICE_TOKEN", "Неверный токен устройства.")
    return create_fall_incident(db, payload, device=device)


@router.get("/api/fall-incidents", response_model=list[FallIncidentRead])
def list_incidents(db: Session = Depends(get_db)):
    return db.query(FallIncident).filter(FallIncident.user_id == 1).order_by(FallIncident.created_at.desc()).all()


@router.post("/api/demo/simulate-fall", response_model=FallIncidentRead)
def simulate_fall(db: Session = Depends(get_db)):
    if not get_settings().enable_demo_mode:
        raise ApiError(403, "DEMO_DISABLED", "Demo mode отключен.")
    payload = FallEventCreate(
        event_timestamp=datetime.now(timezone.utc),
        confidence=0.88,
        sensor_data={"freefall_g": 0.32, "impact_g": 3.1, "stillness_std": 0.08},
    )
    return create_fall_incident(db, payload, is_demo=True)
