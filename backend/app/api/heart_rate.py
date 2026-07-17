"""Heart-rate ingestion and live readout.

Note on "live": the frontend polls this endpoint rather than holding an SSE
stream. EventSource cannot attach an Authorization header, so an SSE version
would have to carry the Supabase access token in the query string, where it
would be captured by every proxy and access log in the path. A short poll keeps
the token in a header. At a 5s cadence the difference is invisible to the user.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import ApiError
from app.models import HeartRateAnomaly, HeartRateReading
from app.schemas.heart_rate import (
    HeartRateAnomalyRead,
    HeartRateBatchCreate,
    HeartRateCreate,
    HeartRateLive,
    HeartRateRead,
    HeartRateSummary,
)
from app.services import hr_simulator
from app.services.heart_rate import (
    add_readings,
    latest_anomaly,
    latest_reading,
    profile_resting_hr,
    resting_baseline,
    score_recent_window,
    summary,
    zone_for,
)

router = APIRouter(prefix="/api/heart-rate", tags=["heart-rate"])

# How much history to backfill when a simulated user has been away. Capped so a
# user returning after a week doesn't trigger a huge synthetic backfill.
MAX_CATCHUP_MINUTES = 30


class ScenarioRequest(BaseModel):
    scenario: str


def _catch_up_simulation(db: Session, user_id: str) -> None:
    """Fill the gap since the last reading with simulated samples.

    Only runs when HR_SOURCE=simulated. With real hardware the device pushes and
    this is a no-op, which is why the endpoints below never branch on source.
    """
    settings = get_settings()
    if settings.hr_source != "simulated":
        return

    now = datetime.now(timezone.utc)
    last = latest_reading(db, user_id)
    interval = timedelta(seconds=settings.hr_sample_interval_seconds)

    if last is None:
        start = now - timedelta(minutes=settings.hr_window_minutes)
    else:
        measured = last.measured_at
        if measured.tzinfo is None:
            measured = measured.replace(tzinfo=timezone.utc)
        # Real readings win. If something is already feeding us fresh data (a
        # device, or a test), do not paper over it with synthetic samples.
        if (now - measured) < interval * 2:
            return
        start = max(measured + interval, now - timedelta(minutes=MAX_CATCHUP_MINUTES))

    resting = profile_resting_hr(db, user_id)
    batch = []
    cursor = start
    while cursor <= now:
        batch.append(hr_simulator.next_reading(user_id, resting, cursor))
        cursor += interval

    if batch:
        add_readings(db, user_id, batch)


@router.post("", response_model=list[HeartRateRead])
def ingest(
    payload: HeartRateBatchCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ingest readings from a device. Scores a window once enough data lands."""
    rows = add_readings(db, user_id, [item.model_dump() for item in payload.readings])
    score_recent_window(db, user_id)
    return rows


@router.get("", response_model=list[HeartRateRead])
def history(
    hours: int = Query(default=6, ge=1, le=168),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(HeartRateReading)
        .filter(HeartRateReading.user_id == user_id, HeartRateReading.measured_at >= since)
        .order_by(HeartRateReading.measured_at.asc())
        .all()
    )


@router.get("/live", response_model=HeartRateLive)
def live(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    _catch_up_simulation(db, user_id)
    score_recent_window(db, user_id)

    reading = latest_reading(db, user_id)
    zone, zone_label = zone_for(reading.bpm if reading else None)

    return HeartRateLive(
        bpm=reading.bpm if reading else None,
        measured_at=reading.measured_at if reading else None,
        source=reading.source if reading else get_settings().hr_source,
        zone=zone,
        zone_label=zone_label,
        resting_baseline=resting_baseline(db, user_id),
        latest_anomaly=latest_anomaly(db, user_id),
    )


@router.get("/summary", response_model=HeartRateSummary)
def stats(
    hours: int = Query(default=24, ge=1, le=168),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return summary(db, user_id, hours)


@router.get("/anomalies", response_model=list[HeartRateAnomalyRead])
def anomalies(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(HeartRateAnomaly)
        .filter(HeartRateAnomaly.user_id == user_id)
        .order_by(HeartRateAnomaly.window_start.desc())
        .limit(limit)
        .all()
    )


@router.post("/scenario", response_model=dict)
def set_scenario(
    payload: ScenarioRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Switch the simulator's pattern. Demo control, not a medical feature."""
    settings = get_settings()
    if not settings.enable_demo_mode or settings.hr_source != "simulated":
        raise ApiError(403, "SIMULATION_DISABLED", "Симуляция отключена.")
    try:
        hr_simulator.set_scenario(user_id, payload.scenario)
    except ValueError:
        raise ApiError(400, "UNKNOWN_SCENARIO", "Неизвестный сценарий.") from None

    # Refill the scoring window with the new rhythm straight away.
    #
    # Without this the window still holds several minutes of the previous
    # rhythm, and since catch-up only tops up the gap since the last reading,
    # the new pattern would take the full window length to become visible. For a
    # demo control that reads as "the button did nothing".
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=settings.hr_window_minutes)
    db.query(HeartRateReading).filter(
        HeartRateReading.user_id == user_id,
        HeartRateReading.measured_at >= window_start,
    ).delete(synchronize_session=False)
    db.commit()

    resting = profile_resting_hr(db, user_id)
    interval = timedelta(seconds=settings.hr_sample_interval_seconds)
    batch = []
    cursor = window_start
    while cursor <= now:
        batch.append(hr_simulator.next_reading(user_id, resting, cursor))
        cursor += interval
    add_readings(db, user_id, batch)
    score_recent_window(db, user_id)

    return {"scenario": payload.scenario, "available": hr_simulator.SCENARIOS}


@router.get("/scenario", response_model=dict)
def get_scenario(user_id: str = Depends(get_current_user)):
    return {
        "scenario": hr_simulator.get_scenario(user_id),
        "available": hr_simulator.SCENARIOS,
        "source": get_settings().hr_source,
    }
