from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, default=1)
    name: Mapped[str] = mapped_column(String(120), default="Азамат")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    biological_sex: Mapped[str | None] = mapped_column(String(40), nullable=True)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_level: Mapped[str] = mapped_column(String(40), default="Moderate")
    primary_goal: Mapped[str] = mapped_column(String(160), default="Общее здоровье")
    health_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    known_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    injuries_or_limitations: Mapped[str | None] = mapped_column(Text, nullable=True)
    dietary_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    sleep_hours: Mapped[float] = mapped_column(Float)
    sleep_quality: Mapped[int] = mapped_column(Integer)
    energy_level: Mapped[int] = mapped_column(Integer)
    stress_level: Mapped[int] = mapped_column(Integer)
    muscle_soreness: Mapped[int] = mapped_column(Integer)
    pain_or_discomfort: Mapped[str | None] = mapped_column(Text, nullable=True)
    planned_activity: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    checkin_id: Mapped[int | None] = mapped_column(ForeignKey("daily_checkins.id"), nullable=True)
    recommendation_type: Mapped[str] = mapped_column(String(60), default="daily_plan")
    structured_result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ECGAnalysis(Base):
    __tablename__ = "ecg_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    original_filename: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(40), default="completed")
    document_summary: Mapped[str] = mapped_column(Text)
    structured_result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    name: Mapped[str] = mapped_column(String(120))
    relationship: Mapped[str] = mapped_column(String(120))
    telegram_chat_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    pairing_code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(40), default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    name: Mapped[str] = mapped_column(String(120))
    device_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    device_token_hash: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(40), default="active")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class FallIncident(Base):
    __tablename__ = "fall_incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, default=1, index=True)
    device_id: Mapped[int | None] = mapped_column(ForeignKey("devices.id"), nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    sensor_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="detected")
    telegram_notification_status: Mapped[str] = mapped_column(String(60), default="not_configured")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
