from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    ai_mode: str
    app_env: str
    # Served rather than hardcoded in the frontend: the bot username lives in the
    # backend's .env, and a second copy in the UI silently drifts out of sync,
    # leaving users a /start link to a bot that doesn't exist.
    telegram_bot_username: str
    telegram_configured: bool


class MessageResponse(BaseModel):
    ok: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class TimestampedModel(OrmModel):
    created_at: datetime


class Source(BaseModel):
    """A guideline excerpt the model was grounded on. Rendered as a citation."""

    title: str
    org: str
    url: str
    year: Optional[int] = None
    section: Optional[str] = None
    quote: Optional[str] = None


class FeatureContribution(BaseModel):
    """One feature's share of an anomaly score, in plain Russian for the UI.

    `weight` is the normalised share across the window's features and sums to ~1.
    """

    feature: str
    label: str
    value: float
    baseline: Optional[float] = None
    deviation: float
    weight: float
    direction: Literal["above", "below", "normal"]
    explanation: str
