from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import UserProfile
from app.schemas.profile import UserProfileRead, UserProfileUpdate
from app.services.seed import ensure_demo_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserProfileRead)
def get_profile(db: Session = Depends(get_db)):
    return ensure_demo_profile(db)


@router.put("", response_model=UserProfileRead)
def update_profile(payload: UserProfileUpdate, db: Session = Depends(get_db)):
    profile = ensure_demo_profile(db)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
