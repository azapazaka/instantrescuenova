from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import ApiError
from app.models import AIRecommendation, DailyCheckIn
from app.schemas.recommendations import (
    AIRecommendationRead,
    DailyCheckInCreate,
    DailyCheckInRead,
    RecommendationCreate,
)
from app.services.ai import MockAIProvider
from app.services.seed import ensure_demo_profile

router = APIRouter(tags=["recommendations"])


@router.post("/api/checkins", response_model=DailyCheckInRead)
def create_checkin(payload: DailyCheckInCreate, db: Session = Depends(get_db)):
    checkin = DailyCheckIn(user_id=1, **payload.model_dump())
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


@router.get("/api/checkins", response_model=list[DailyCheckInRead])
def list_checkins(db: Session = Depends(get_db)):
    return db.query(DailyCheckIn).filter(DailyCheckIn.user_id == 1).order_by(DailyCheckIn.created_at.desc()).all()


@router.post("/api/recommendations", response_model=AIRecommendationRead)
def create_recommendation(payload: RecommendationCreate, db: Session = Depends(get_db)):
    profile = ensure_demo_profile(db)
    checkin = None
    if payload.checkin_id:
        checkin = db.query(DailyCheckIn).filter(DailyCheckIn.id == payload.checkin_id, DailyCheckIn.user_id == 1).first()
        if not checkin:
            raise ApiError(404, "CHECKIN_NOT_FOUND", "Check-in не найден.")
    else:
        checkin = db.query(DailyCheckIn).filter(DailyCheckIn.user_id == 1).order_by(DailyCheckIn.created_at.desc()).first()

    result = MockAIProvider().generate_health_recommendation(profile, checkin)
    recommendation = AIRecommendation(
        user_id=1,
        checkin_id=checkin.id if checkin else None,
        recommendation_type="daily_plan",
        structured_result=result.model_dump(),
    )
    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)
    return recommendation


@router.get("/api/recommendations", response_model=list[AIRecommendationRead])
def list_recommendations(db: Session = Depends(get_db)):
    return db.query(AIRecommendation).filter(AIRecommendation.user_id == 1).order_by(AIRecommendation.created_at.desc()).all()


@router.get("/api/recommendations/{recommendation_id}", response_model=AIRecommendationRead)
def get_recommendation(recommendation_id: int, db: Session = Depends(get_db)):
    recommendation = db.query(AIRecommendation).filter(AIRecommendation.id == recommendation_id, AIRecommendation.user_id == 1).first()
    if not recommendation:
        raise ApiError(404, "RECOMMENDATION_NOT_FOUND", "Рекомендация не найдена.")
    return recommendation
