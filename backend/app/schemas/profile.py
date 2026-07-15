from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import OrmModel


class UserProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int | None = Field(default=None, ge=18, le=120)
    biological_sex: str | None = None
    height_cm: int | None = Field(default=None, ge=80, le=240)
    weight_kg: float | None = Field(default=None, ge=30, le=250)
    activity_level: str = "Moderate"
    primary_goal: str = "Общее здоровье"
    health_goals: str | None = None
    known_conditions: str | None = None
    injuries_or_limitations: str | None = None
    dietary_preferences: str | None = None


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfileRead(UserProfileBase, OrmModel):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
