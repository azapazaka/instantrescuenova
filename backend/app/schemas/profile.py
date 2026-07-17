from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class UserProfileUpdate(BaseModel):
    """What a user may submit. Constraints are intentionally strict here."""

    name: str = Field(min_length=1, max_length=120)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    biological_sex: Optional[str] = None
    height_cm: Optional[int] = Field(default=None, ge=80, le=240)
    weight_kg: Optional[float] = Field(default=None, ge=30, le=250)
    activity_level: str = "Moderate"
    primary_goal: str = "Общее здоровье"
    health_goals: Optional[str] = None
    known_conditions: Optional[str] = None
    injuries_or_limitations: Optional[str] = None
    dietary_preferences: Optional[str] = None
    resting_hr_baseline: Optional[float] = Field(default=None, ge=30, le=120)


class UserProfileRead(OrmModel):
    """What we return. Must NOT reuse the update constraints.

    A profile is created empty on first login, so `name` is legitimately "" until
    the user fills it in. Enforcing min_length=1 on read made GET /api/profile
    fail validation and return 500 for every brand-new account.
    """

    id: int
    user_id: str
    name: str
    age: Optional[int]
    biological_sex: Optional[str]
    height_cm: Optional[int]
    weight_kg: Optional[float]
    activity_level: str
    primary_goal: str
    health_goals: Optional[str]
    known_conditions: Optional[str]
    injuries_or_limitations: Optional[str]
    dietary_preferences: Optional[str]
    resting_hr_baseline: Optional[float]
    created_at: datetime
    updated_at: datetime
