from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class EmergencyContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    relationship: str = Field(min_length=1, max_length=120)
    telegram_username: Optional[str] = Field(default=None, max_length=120)


class EmergencyContactRead(OrmModel):
    id: int
    user_id: str
    name: str
    relationship: str
    telegram_username: Optional[str]
    telegram_chat_id: Optional[str]
    pairing_code: str
    status: str
    created_at: datetime
    updated_at: datetime


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class DeviceRead(OrmModel):
    id: int
    user_id: str
    name: str
    device_id: str
    status: str
    last_seen_at: Optional[datetime]
    created_at: datetime


class DeviceCreated(DeviceRead):
    device_secret: str


class FallEventCreate(BaseModel):
    event_timestamp: datetime
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    sensor_data: dict = Field(default_factory=dict)


class NotificationAttempt(BaseModel):
    contact_id: int
    contact_name: str
    ok: bool
    detail: str


class FallIncidentRead(OrmModel):
    id: int
    user_id: str
    device_id: Optional[int]
    event_timestamp: datetime
    confidence: Optional[float]
    sensor_payload: dict
    status: str
    telegram_notification_status: str
    notification_detail: list[NotificationAttempt] = Field(default_factory=list)
    hr_context: Optional[dict] = None
    created_at: datetime
