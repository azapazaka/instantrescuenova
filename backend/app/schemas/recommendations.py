from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.common import FeatureContribution, OrmModel, Source


class DailyCheckInCreate(BaseModel):
    sleep_hours: float = Field(ge=0, le=16)
    sleep_quality: int = Field(ge=1, le=10)
    energy_level: int = Field(ge=1, le=10)
    stress_level: int = Field(ge=1, le=10)
    muscle_soreness: int = Field(ge=1, le=10)
    pain_or_discomfort: Optional[str] = None
    planned_activity: Optional[str] = None
    notes: Optional[str] = None


class DailyCheckInRead(DailyCheckInCreate, OrmModel):
    id: int
    user_id: str
    created_at: datetime


class RecommendationCreate(BaseModel):
    checkin_id: Optional[int] = None


class Readiness(BaseModel):
    level: Literal["low", "moderate", "high"]
    explanation: str


class MovementPlan(BaseModel):
    title: str
    recommendation: str
    intensity: Literal["low", "moderate", "high"]
    duration: str
    reasoning: str
    sources: list[Source] = Field(default_factory=list)


class RecommendationBlock(BaseModel):
    recommendation: str
    reasoning: str
    sources: list[Source] = Field(default_factory=list)


class HeartRateInsight(BaseModel):
    """What the anomaly model saw, in the user's language.

    `contributions` carries the per-feature attributions so the UI can show why
    the plan changed, rather than asserting a conclusion the user can't check.
    """

    summary: str
    severity: Literal["normal", "watch", "elevated", "high"]
    average_bpm: Optional[float] = None
    resting_bpm: Optional[float] = None
    contributions: list[FeatureContribution] = Field(default_factory=list)


class HealthRecommendationResult(BaseModel):
    summary: str
    readiness: Readiness
    today_focus: str
    movement: MovementPlan
    recovery: RecommendationBlock
    nutrition: RecommendationBlock
    sleep: RecommendationBlock
    things_to_avoid: list[str]
    important_notes: list[str]
    medical_safety_message: Optional[str] = None
    heart_rate_insight: Optional[HeartRateInsight] = None


class AIRecommendationRead(OrmModel):
    id: int
    user_id: str
    checkin_id: Optional[int]
    recommendation_type: str
    structured_result: HealthRecommendationResult
    sources: list[Source] = Field(default_factory=list)
    ai_mode: str = "mock"
    created_at: datetime
