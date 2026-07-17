"""Heart rate ingestion, scoring and explainability."""

from datetime import datetime, timedelta, timezone

from app.services.anomaly import score_window
from app.services.features import bpm_to_rr, extract_features


def _readings(bpms, start=None):
    # End the series at "now" so the simulator's catch-up does not overwrite it.
    start = start or datetime.now(timezone.utc) - timedelta(seconds=5 * len(bpms))
    return {
        "readings": [
            {
                "bpm": bpm,
                "source": "device",
                "measured_at": (start + timedelta(seconds=5 * i)).isoformat(),
            }
            for i, bpm in enumerate(bpms)
        ]
    }


def test_ingest_stores_readings(client):
    response = client.post("/api/heart-rate", json=_readings([70, 72, 71, 69, 73]))
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_ingest_rejects_impossible_bpm(client):
    response = client.post("/api/heart-rate", json={"readings": [{"bpm": 400}]})
    assert response.status_code == 422


def test_live_returns_zone(client):
    client.post("/api/heart-rate", json=_readings([72] * 20))
    data = client.get("/api/heart-rate/live").json()
    assert data["zone"] == "normal"
    assert data["zone_label"] == "Норма покоя"


def test_live_reports_high_zone(client):
    client.post("/api/heart-rate", json=_readings([118] * 20))
    assert client.get("/api/heart-rate/live").json()["zone"] == "high"


def test_summary_counts_readings(client):
    client.post("/api/heart-rate", json=_readings([60, 80, 70]))
    data = client.get("/api/heart-rate/summary").json()
    assert data["reading_count"] == 3
    assert data["min_bpm"] == 60
    assert data["max_bpm"] == 80


def test_scoring_needs_enough_data(client):
    """Too few readings must yield no anomaly rather than a fabricated one."""
    client.post("/api/heart-rate", json=_readings([70, 71]))
    assert client.get("/api/heart-rate/anomalies").json() == []


def test_window_scoring_produces_contributions(client):
    client.post("/api/heart-rate", json=_readings([72 + (i % 3) for i in range(40)]))
    anomalies = client.get("/api/heart-rate/anomalies").json()
    assert anomalies, "expected a scored window"

    latest = anomalies[0]
    assert 0.0 <= latest["anomaly_score"] <= 1.0
    assert latest["contributions"], "a score with no explanation is unusable"
    # Attribution weights are shares of one window and must sum to ~1.
    assert abs(sum(c["weight"] for c in latest["contributions"]) - 1.0) < 0.05
    assert all(c["explanation"] for c in latest["contributions"])


# ------------------------------------------------------- unit-level scoring
def test_features_reject_short_window():
    assert extract_features(bpm_to_rr([70, 71])) is None


def test_steady_normal_pulse_is_not_flagged():
    features = extract_features(bpm_to_rr([70 + (i % 3) for i in range(60)]))
    assert score_window(features)["severity"] == "normal"


def test_sustained_tachycardia_is_escalated_by_rate_rule():
    """The model alone scores this normal (MIT-BIH has almost no tachycardia),
    so the clinical rate rule is what must catch it."""
    features = extract_features(bpm_to_rr([110 + (i % 3) for i in range(60)]))
    result = score_window(features)
    assert result["severity"] in {"elevated", "high"}
    assert result["rate_flag"] is not None


def test_irregular_rhythm_raises_score():
    """AFib-like irregularity: alternating long/short intervals."""
    bpms = [60 if i % 2 else 105 for i in range(60)]
    result = score_window(extract_features(bpm_to_rr(bpms)))
    assert result["severity"] in {"elevated", "high"}
    top = result["contributions"][0]
    assert top["feature"] in {"pnn50", "rmssd", "sdnn", "hr_range"}


def test_explanation_uses_healthy_baseline_by_default():
    features = extract_features(bpm_to_rr([70] * 60))
    assert score_window(features)["baseline_source"] == "healthy_population"
