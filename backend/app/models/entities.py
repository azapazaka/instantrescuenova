from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.core.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Supabase auth.users.id.
#
# In Postgres this column really is `uuid` and carries a foreign key to
# auth.users(id), so binding it as VARCHAR makes inserts fail outright —
# Postgres will not implicitly cast varchar to uuid. SQLite has no uuid type,
# and the tests run on SQLite, hence the variant. Values stay plain `str` in
# Python either way (as_uuid=False).
UserId = String(36).with_variant(UUID(as_uuid=False), "postgresql")

# Postgres uses bigint identity columns; SQLite only autoincrements a column
# declared exactly INTEGER PRIMARY KEY, so BIGINT there breaks inserts. The
# variant keeps one model definition working against both.
PrimaryKey = BigInteger().with_variant(Integer, "sqlite")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, unique=True, index=True)
    name: Mapped[str] = mapped_column(Text, default="")
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    biological_sex: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    height_cm: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    activity_level: Mapped[str] = mapped_column(Text, default="Moderate")
    primary_goal: Mapped[str] = mapped_column(Text, default="Общее здоровье")
    health_goals: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    known_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    injuries_or_limitations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dietary_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resting_hr_baseline: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    sleep_hours: Mapped[float] = mapped_column(Float)
    sleep_quality: Mapped[int] = mapped_column(Integer)
    energy_level: Mapped[int] = mapped_column(Integer)
    stress_level: Mapped[int] = mapped_column(Integer)
    muscle_soreness: Mapped[int] = mapped_column(Integer)
    pain_or_discomfort: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    planned_activity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    checkin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("daily_checkins.id"), nullable=True)
    recommendation_type: Mapped[str] = mapped_column(Text, default="daily_plan")
    structured_result: Mapped[dict] = mapped_column(JSON)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    ai_mode: Mapped[str] = mapped_column(Text, default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HealthDocumentAnalysis(Base):
    """Analysis of an uploaded medical PDF. The source PDF itself is never stored."""

    __tablename__ = "health_document_analyses"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    original_filename: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="completed")
    document_summary: Mapped[str] = mapped_column(Text)
    structured_result: Mapped[dict] = mapped_column(JSON)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    ai_mode: Mapped[str] = mapped_column(Text, default="mock")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    name: Mapped[str] = mapped_column(Text)
    relationship: Mapped[str] = mapped_column(Text)
    telegram_username: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    telegram_chat_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pairing_code: Mapped[str] = mapped_column(Text, unique=True, index=True)
    status: Mapped[str] = mapped_column(Text, default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    name: Mapped[str] = mapped_column(Text)
    device_id: Mapped[str] = mapped_column(Text, unique=True, index=True)
    device_token_hash: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="active")
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class FallIncident(Base):
    __tablename__ = "fall_incidents"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"), nullable=True)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sensor_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(Text, default="detected")
    telegram_notification_status: Mapped[str] = mapped_column(Text, default="not_configured")
    notification_detail: Mapped[list] = mapped_column(JSON, default=list)
    hr_context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HeartRateReading(Base):
    __tablename__ = "heart_rate_readings"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    bpm: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(Text, default="simulated")
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class HeartRateAnomaly(Base):
    """One scored window. `contributions` is what the explainability UI renders."""

    __tablename__ = "heart_rate_anomalies"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    user_id: Mapped[str] = mapped_column(UserId, index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    anomaly_score: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(Text, default="normal")
    predicted_label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rate_flag: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    baseline_source: Mapped[str] = mapped_column(Text, default="healthy_population")
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    contributions: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class GuidelineChunk(Base):
    """Curated WHO/ESC/AHA guideline excerpt used as RAG grounding.

    The `embedding` column exists in Postgres (pgvector) but is intentionally not
    mapped here: pgvector has no SQLite equivalent and the tests run on SQLite.
    Vector search goes through raw SQL in app/services/rag.py.
    """

    __tablename__ = "guideline_chunks"

    id: Mapped[int] = mapped_column(PrimaryKey, primary_key=True)
    slug: Mapped[str] = mapped_column(Text, unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    org: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
