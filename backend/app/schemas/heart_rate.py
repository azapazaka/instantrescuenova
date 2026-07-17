from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.common import FeatureContribution, OrmModel


class HeartRateCreate(BaseModel):
    # Bounds are deliberately wide: a real sensor artefact should be stored and
    # flagged by the model, not silently rejected at the edge.
    bpm: float = Field(ge=20, le=250)
    source: str = "device"
    context: Optional[str] = None
    measured_at: Optional[datetime] = None


class HeartRateBatchCreate(BaseModel):
    readings: list[HeartRateCreate] = Field(min_length=1, max_length=1000)


class HeartRateRead(OrmModel):
    id: int
    user_id: str
    bpm: float
    source: str
    context: Optional[str]
    measured_at: datetime


class HeartRateAnomalyRead(OrmModel):
    id: int
    user_id: str
    window_start: datetime
    window_end: datetime
    anomaly_score: float
    severity: Literal["normal", "watch", "elevated", "high"]
    predicted_label: Optional[str]
    rate_flag: Optional[str] = None
    baseline_source: str = "healthy_population"
    features: dict
    contributions: list[FeatureContribution]
    created_at: datetime


class HeartRateLive(BaseModel):
    """Payload for the dashboard's live bar."""

    bpm: Optional[float]
    measured_at: Optional[datetime]
    source: str
    zone: Literal["low", "normal", "elevated", "high", "unknown"]
    zone_label: str
    resting_baseline: Optional[float] = None
    latest_anomaly: Optional[HeartRateAnomalyRead] = None


class HeartRateSummary(BaseModel):
    average_bpm: Optional[float]
    min_bpm: Optional[float]
    max_bpm: Optional[float]
    resting_bpm: Optional[float]
    reading_count: int
    window_hours: int
