from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class DailyCheckInCreate(BaseModel):
    sleep_hours: float = Field(ge=0, le=16)
    sleep_quality: int = Field(ge=1, le=10)
    energy_level: int = Field(ge=1, le=10)
    stress_level: int = Field(ge=1, le=10)
    muscle_soreness: int = Field(ge=1, le=10)
    pain_or_discomfort: str | None = None
    planned_activity: str | None = None
    notes: str | None = None


class DailyCheckInRead(DailyCheckInCreate, OrmModel):
    id: int
    user_id: int
    created_at: datetime


class RecommendationCreate(BaseModel):
    checkin_id: int | None = None


class Readiness(BaseModel):
    level: Literal["low", "moderate", "high"]
    explanation: str


class MovementPlan(BaseModel):
    title: str
    recommendation: str
    intensity: Literal["low", "moderate", "high"]
    duration: str
    reasoning: str


class RecommendationBlock(BaseModel):
    recommendation: str
    reasoning: str


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
    medical_safety_message: str | None = None


class AIRecommendationRead(OrmModel):
    id: int
    user_id: int
    checkin_id: int | None
    recommendation_type: str
    structured_result: HealthRecommendationResult
    created_at: datetime
