from sqlalchemy.orm import Session

from app.models import UserProfile


def ensure_demo_profile(db: Session) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == 1).first()
    if profile:
        return profile
    profile = UserProfile(
        user_id=1,
        name="Азамат",
        age=38,
        biological_sex="male",
        height_cm=176,
        weight_kg=79,
        activity_level="Moderate",
        primary_goal="Общее здоровье",
        health_goals="Больше энергии, безопасная активность и восстановление",
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile
