from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel, Source


class DetectedMeasurement(BaseModel):
    name: str
    value: str
    reference_range: Optional[str] = None
    status: Literal["normal", "borderline", "out_of_range", "unknown"] = "unknown"
    source_page: Optional[int] = None


class Observation(BaseModel):
    title: str
    description: str
    importance: Literal["low", "moderate", "high"]
    source_page: Optional[int] = None


class LifestyleAdvice(BaseModel):
    """Diet / sport guidance derived from the document, grounded in guidelines."""

    recommendation: str
    reasoning: str
    sources: list[Source] = Field(default_factory=list)


class DocumentQuality(BaseModel):
    level: Literal["poor", "fair", "good"]
    explanation: str


class HealthDocumentResult(BaseModel):
    document_type: str
    analysis_status: Literal["completed", "limited"]
    document_summary: str
    detected_measurements: list[DetectedMeasurement]
    observations: list[Observation]
    nutrition_advice: list[LifestyleAdvice] = Field(default_factory=list)
    activity_advice: list[LifestyleAdvice] = Field(default_factory=list)
    document_quality: DocumentQuality
    recommended_next_steps: list[str]
    questions_for_doctor: list[str]
    urgent_flags: list[str]
    limitations: list[str]


class HealthDocumentRead(OrmModel):
    id: int
    user_id: str
    original_filename: str
    status: str
    document_summary: str
    structured_result: HealthDocumentResult
    sources: list[Source] = Field(default_factory=list)
    ai_mode: str
    created_at: datetime
