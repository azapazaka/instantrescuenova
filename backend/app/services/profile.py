from sqlalchemy.orm import Session

from app.models import UserProfile


def ensure_profile(db: Session, user_id: str, name: str = "") -> UserProfile:
    """Return the caller's profile, creating an empty one on first access.

    Signup only creates an auth.users row, so the first authenticated request is
    where the profile row appears. Callers must pass a verified user_id.
    """
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        return profile

    profile = UserProfile(user_id=user_id, name=name)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
