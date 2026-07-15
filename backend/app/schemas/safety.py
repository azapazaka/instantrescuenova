from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class EmergencyContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    relationship: str = Field(min_length=1, max_length=120)
    telegram_username: str | None = Field(default=None, max_length=120)


class EmergencyContactRead(OrmModel):
    id: int
    user_id: int
    name: str
    relationship: str
    telegram_username: str | None
    telegram_chat_id: str | None
    pairing_code: str
    status: str
    created_at: datetime
    updated_at: datetime


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DeviceRead(OrmModel):
    id: int
    user_id: int
    name: str
    device_id: str
    status: str
    last_seen_at: datetime | None
    created_at: datetime


class DeviceCreated(DeviceRead):
    device_secret: str


class FallEventCreate(BaseModel):
    event_timestamp: datetime
    confidence: float | None = Field(default=None, ge=0, le=1)
    sensor_data: dict = Field(default_factory=dict)


class FallIncidentRead(OrmModel):
    id: int
    user_id: int
    device_id: int | None
    event_timestamp: datetime
    confidence: float | None
    sensor_payload: dict
    status: str
    telegram_notification_status: str
    created_at: datetime
