"""Heart-rate ingestion, windowing, baselines and scoring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import HeartRateAnomaly, HeartRateReading, UserProfile
from app.services.anomaly import score_window
from app.services.features import FEATURE_NAMES, bpm_to_rr, extract_features

# Resting-pulse zones for a general adult population. These are display bands,
# not a diagnosis, and the UI labels them as such.
ZONES = [
    (0, 50, "low", "Ниже нормы"),
    (50, 90, "normal", "Норма покоя"),
    (90, 110, "elevated", "Повышен"),
    (110, 999, "high", "Высокий"),
]

MIN_READINGS_FOR_WINDOW = 12
MIN_WINDOWS_FOR_PERSONAL_BASELINE = 8


def zone_for(bpm: Optional[float]) -> tuple[str, str]:
    if bpm is None:
        return "unknown", "Нет данных"
    for low, high, key, label in ZONES:
        if low <= bpm < high:
            return key, label
    return "unknown", "Нет данных"


def add_readings(db: Session, user_id: str, readings: list[dict]) -> list[HeartRateReading]:
    now = datetime.now(timezone.utc)
    rows = [
        HeartRateReading(
            user_id=user_id,
            bpm=item["bpm"],
            source=item.get("source", "device"),
            context=item.get("context"),
            measured_at=item.get("measured_at") or now,
        )
        for item in readings
    ]
    db.add_all(rows)
    db.commit()
    return rows


def recent_readings(db: Session, user_id: str, minutes: int) -> list[HeartRateReading]:
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    return (
        db.query(HeartRateReading)
        .filter(HeartRateReading.user_id == user_id, HeartRateReading.measured_at >= since)
        .order_by(HeartRateReading.measured_at.asc())
        .all()
    )


def latest_reading(db: Session, user_id: str) -> Optional[HeartRateReading]:
    return (
        db.query(HeartRateReading)
        .filter(HeartRateReading.user_id == user_id)
        .order_by(HeartRateReading.measured_at.desc())
        .first()
    )


def resting_baseline(db: Session, user_id: str) -> Optional[float]:
    """Resting pulse = 10th percentile of the last 7 days.

    A plain average would be dragged up by activity; the low tail is a better
    stand-in for true resting rate without needing sleep staging.
    """
    since = datetime.now(timezone.utc) - timedelta(days=7)
    values = [
        row.bpm
        for row in db.query(HeartRateReading.bpm)
        .filter(HeartRateReading.user_id == user_id, HeartRateReading.measured_at >= since)
        .all()
    ]
    if len(values) < 30:
        return None
    values.sort()
    return round(values[int(len(values) * 0.10)], 1)


def personal_baseline(db: Session, user_id: str) -> Optional[dict[str, dict[str, float]]]:
    """Feature means/stds from this user's own recent normal windows.

    Returns None until there is enough history — scoring against a baseline built
    from three readings would flag everything.
    """
    rows = (
        db.query(HeartRateAnomaly)
        .filter(HeartRateAnomaly.user_id == user_id, HeartRateAnomaly.severity == "normal")
        .order_by(HeartRateAnomaly.window_start.desc())
        .limit(200)
        .all()
    )
    if len(rows) < MIN_WINDOWS_FOR_PERSONAL_BASELINE:
        return None

    mean: dict[str, float] = {}
    std: dict[str, float] = {}
    for name in FEATURE_NAMES:
        values = [float(r.features[name]) for r in rows if name in (r.features or {})]
        if len(values) < MIN_WINDOWS_FOR_PERSONAL_BASELINE:
            return None
        avg = sum(values) / len(values)
        variance = sum((v - avg) ** 2 for v in values) / (len(values) - 1)
        mean[name] = avg
        std[name] = max(variance**0.5, 1e-6)
    return {"mean": mean, "std": std}


def score_recent_window(db: Session, user_id: str) -> Optional[HeartRateAnomaly]:
    """Score the most recent window and persist it.

    Returns None when there is not enough data yet — the caller shows "collecting
    data" rather than a fabricated score.
    """
    settings = get_settings()
    readings = recent_readings(db, user_id, settings.hr_window_minutes)
    if len(readings) < MIN_READINGS_FOR_WINDOW:
        return None

    features = extract_features(bpm_to_rr([r.bpm for r in readings]))
    if features is None:
        return None

    result = score_window(features, personal_baseline(db, user_id))
    anomaly = HeartRateAnomaly(
        user_id=user_id,
        window_start=readings[0].measured_at,
        window_end=readings[-1].measured_at,
        anomaly_score=result["anomaly_score"],
        severity=result["severity"],
        predicted_label=result["predicted_label"],
        rate_flag=result["rate_flag"],
        baseline_source=result["baseline_source"],
        features=result["features"],
        contributions=result["contributions"],
    )
    db.add(anomaly)
    db.commit()
    db.refresh(anomaly)
    return anomaly


def latest_anomaly(db: Session, user_id: str) -> Optional[HeartRateAnomaly]:
    return (
        db.query(HeartRateAnomaly)
        .filter(HeartRateAnomaly.user_id == user_id)
        .order_by(HeartRateAnomaly.window_start.desc())
        .first()
    )


def summary(db: Session, user_id: str, hours: int = 24) -> dict:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    values = [
        row.bpm
        for row in db.query(HeartRateReading.bpm)
        .filter(HeartRateReading.user_id == user_id, HeartRateReading.measured_at >= since)
        .all()
    ]
    if not values:
        return {
            "average_bpm": None, "min_bpm": None, "max_bpm": None,
            "resting_bpm": resting_baseline(db, user_id),
            "reading_count": 0, "window_hours": hours,
        }
    return {
        "average_bpm": round(sum(values) / len(values), 1),
        "min_bpm": round(min(values), 1),
        "max_bpm": round(max(values), 1),
        "resting_bpm": resting_baseline(db, user_id),
        "reading_count": len(values),
        "window_hours": hours,
    }


def profile_resting_hr(db: Session, user_id: str) -> Optional[float]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    return profile.resting_hr_baseline if profile else None
