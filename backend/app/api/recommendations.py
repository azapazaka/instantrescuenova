from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import AIRecommendation, DailyCheckIn
from app.schemas.recommendations import (
    AIRecommendationRead,
    DailyCheckInCreate,
    DailyCheckInRead,
    RecommendationCreate,
)
from app.services.ai import get_provider
from app.services.heart_rate import latest_anomaly, resting_baseline, summary
from app.services.profile import ensure_profile
from app.services.rag import retrieve

router = APIRouter(tags=["recommendations"])


@router.post("/api/checkins", response_model=DailyCheckInRead)
def create_checkin(
    payload: DailyCheckInCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    checkin = DailyCheckIn(user_id=user_id, **payload.model_dump())
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


@router.get("/api/checkins", response_model=list[DailyCheckInRead])
def list_checkins(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(DailyCheckIn)
        .filter(DailyCheckIn.user_id == user_id)
        .order_by(DailyCheckIn.created_at.desc())
        .all()
    )


def _hr_insight(db: Session, user_id: str) -> Optional[dict]:
    """Package the latest anomaly window for the prompt and the response."""
    anomaly = latest_anomaly(db, user_id)
    if not anomaly:
        return None
    stats = summary(db, user_id, hours=24)
    return {
        "severity": anomaly.severity,
        "anomaly_score": anomaly.anomaly_score,
        "contributions": anomaly.contributions,
        "average_bpm": stats["average_bpm"],
        "resting_bpm": resting_baseline(db, user_id),
        "summary": f"Последнее окно оценено как «{anomaly.severity}».",
    }


def _retrieval_query(profile, checkin, insight) -> str:
    """Build the RAG query from what actually varies between users."""
    parts = ["рекомендации по образу жизни для сердца"]
    if profile.age and profile.age >= 65:
        parts.append("пожилые люди 65 лет физическая активность")
    if profile.known_conditions:
        parts.append(profile.known_conditions)
    if checkin and checkin.pain_or_discomfort:
        parts.append(checkin.pain_or_discomfort)
    if insight and insight["severity"] != "normal":
        parts.append("повышенный пульс вариабельность ритма аритмия")
    return ". ".join(parts)


def _collect_sources(result) -> list:
    """Deduplicate the per-block citations into one list for the response."""
    seen: dict[str, object] = {}
    for block in (result.movement, result.recovery, result.nutrition, result.sleep):
        for source in block.sources:
            seen.setdefault(source.url, source)
    return list(seen.values())


@router.post("/api/recommendations", response_model=AIRecommendationRead)
def create_recommendation(
    payload: RecommendationCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = ensure_profile(db, user_id)

    if payload.checkin_id:
        checkin = (
            db.query(DailyCheckIn)
            .filter(DailyCheckIn.id == payload.checkin_id, DailyCheckIn.user_id == user_id)
            .first()
        )
        if not checkin:
            raise ApiError(404, "CHECKIN_NOT_FOUND", "Check-in не найден.")
    else:
        checkin = (
            db.query(DailyCheckIn)
            .filter(DailyCheckIn.user_id == user_id)
            .order_by(DailyCheckIn.created_at.desc())
            .first()
        )

    insight = _hr_insight(db, user_id)
    chunks, _mode = retrieve(db, _retrieval_query(profile, checkin, insight))

    provider = get_provider()
    result = provider.generate_health_recommendation(profile, checkin, insight, chunks)

    recommendation = AIRecommendation(
        user_id=user_id,
        checkin_id=checkin.id if checkin else None,
        recommendation_type="daily_plan",
        structured_result=result.model_dump(mode="json"),
        sources=[s.model_dump(mode="json") for s in _collect_sources(result)],
        ai_mode=provider.mode,
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


@router.get("/api/recommendations", response_model=list[AIRecommendationRead])
def list_recommendations(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AIRecommendation)
        .filter(AIRecommendation.user_id == user_id)
        .order_by(AIRecommendation.created_at.desc())
        .all()
    )


@router.get("/api/recommendations/{recommendation_id}", response_model=AIRecommendationRead)
def get_recommendation(
    recommendation_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recommendation = (
        db.query(AIRecommendation)
        .filter(AIRecommendation.id == recommendation_id, AIRecommendation.user_id == user_id)
        .first()
    )
    if not recommendation:
        raise ApiError(404, "RECOMMENDATION_NOT_FOUND", "Рекомендация не найдена.")
    return recommendation
