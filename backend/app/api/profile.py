from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.profile import UserProfileRead, UserProfileUpdate
from app.services.profile import ensure_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=UserProfileRead)
def get_profile(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    return ensure_profile(db, user_id)


@router.put("", response_model=UserProfileRead)
def update_profile(
    payload: UserProfileUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = ensure_profile(db, user_id)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
