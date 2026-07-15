from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import OrmModel


class ECGMeasurement(BaseModel):
    name: str
    value: str
    source_page: int | None = None


class ECGObservation(BaseModel):
    title: str
    description: str
    importance: Literal["low", "moderate", "high"]
    source_page: int | None = None


class ECGPattern(BaseModel):
    name: str
    explanation: str
    confidence: Literal["low", "moderate", "high"]


class ECGQuality(BaseModel):
    level: Literal["poor", "fair", "good"]
    explanation: str


class ECGAnalysisResult(BaseModel):
    document_type: str
    analysis_status: Literal["completed", "limited"]
    document_summary: str
    detected_measurements: list[ECGMeasurement]
    observations: list[ECGObservation]
    possible_patterns: list[ECGPattern]
    signal_or_document_quality: ECGQuality
    recommended_next_steps: list[str]
    questions_for_doctor: list[str]
    urgent_flags: list[str]
    limitations: list[str]


class ECGAnalysisRead(OrmModel):
    id: int
    user_id: int
    original_filename: str
    status: str
    document_summary: str
    structured_result: ECGAnalysisResult
    created_at: datetime
