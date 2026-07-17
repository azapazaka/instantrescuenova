"""Score a heart-rate window and explain the score.

The explanation is the product here, not a nicety. A number like "anomaly score
0.71" is unusable by an elderly user or their doctor. What they can act on is
"your resting pulse is 18 bpm above your own normal, and that accounts for most
of this flag". So every score carries per-feature attributions, and the UI is
built to show them.

Attribution method: each feature's deviation from baseline (z-score) is weighted
by the trained classifier's importance for that feature, then normalised across
the window. This is a first-order approximation, not SHAP — it is honest about
*which inputs moved*, and cheap enough to run on every window. Its limits are
stated in the README.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.services.features import FEATURE_LABELS, FEATURE_NAMES, FEATURE_UNITS, to_vector

ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "ml" / "artifacts" / "hr_model.joblib"

# Reference baseline for a healthy resting adult.
#
# Deliberately NOT taken from the trained artifact. The artifact's baseline is
# computed from MIT-BIH "normal" windows, but those come from patients recorded
# *because* they have arrhythmias — their normal-rhythm stretches still carry
# unusually high beat-to-beat variability (pNN50 ~26% vs ~12% for a healthy
# adult). Explaining a healthy user's pulse against that baseline produces
# nonsense like "your pNN50 is below normal" for a perfectly ordinary reading.
#
# So: MIT-BIH trains the rhythm classifier (what it is good for), and these
# healthy-population values anchor the explanation shown to the user, until the
# user has enough history for a personal baseline — which beats both.
HEALTHY_BASELINE = {
    "mean": {
        "mean_hr": 72.0, "min_hr": 62.0, "max_hr": 86.0, "sdnn": 50.0,
        "rmssd": 42.0, "pnn50": 12.0, "hr_range": 24.0, "hr_trend_slope": 0.0,
    },
    "std": {
        "mean_hr": 10.0, "min_hr": 9.0, "max_hr": 13.0, "sdnn": 22.0,
        "rmssd": 20.0, "pnn50": 10.0, "hr_range": 12.0, "hr_trend_slope": 6.0,
    },
}

# Features where "higher" is the clinically interesting direction get a plain
# reading; variability features read the other way (low HRV is the concern).
LOWER_IS_CONCERNING = {"sdnn", "rmssd"}

SEVERITY_THRESHOLDS = [(0.75, "high"), (0.55, "elevated"), (0.35, "watch")]

# Rate-based severity floors, applied on top of the model score.
#
# The model is trained on MIT-BIH, which is rhythm-annotated and contains almost
# no sustained tachycardia (6 windows out of 1639). It therefore cannot learn
# that a resting pulse of 110 matters, and in testing it scored exactly that as
# "normal". Rate is not something we need a model to judge — the thresholds are
# long-settled clinical convention, so we apply them as rules and let the model
# do the part rules cannot: spotting irregular rhythm.
#
# (min_mean_hr, max_mean_hr, severity floor, reason)
RATE_RULES = [
    (120.0, 999.0, "high", "устойчиво высокий пульс покоя"),
    (100.0, 120.0, "elevated", "пульс покоя выше 100 уд/мин (тахикардия)"),
    (0.0, 45.0, "elevated", "пульс покоя ниже 45 уд/мин (брадикардия)"),
    (45.0, 50.0, "watch", "пульс покоя ниже 50 уд/мин"),
]

_SEVERITY_ORDER = ["normal", "watch", "elevated", "high"]


def _apply_rate_rules(mean_hr: float, severity: str) -> tuple[str, Optional[str]]:
    """Raise severity to the clinical floor for this heart rate, never lower it."""
    for low, high, floor, reason in RATE_RULES:
        if low <= mean_hr < high:
            if _SEVERITY_ORDER.index(floor) > _SEVERITY_ORDER.index(severity):
                return floor, reason
            return severity, reason
    return severity, None


@lru_cache(maxsize=1)
def _artifact() -> Optional[dict]:
    """Load the trained model once. Returns None if training hasn't been run."""
    if not ARTIFACT_PATH.exists():
        return None
    try:
        import joblib

        return joblib.load(ARTIFACT_PATH)
    except Exception:
        # A corrupt or version-mismatched artifact must not take the API down;
        # scoring falls back to the baseline-only path below.
        return None


def _severity(score: float) -> str:
    for threshold, name in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return name
    return "normal"


def _describe(feature: str, value: float, baseline: float, z: float) -> tuple[str, str]:
    unit = FEATURE_UNITS[feature]
    label = FEATURE_LABELS[feature]

    if abs(z) < 1.0:
        return "normal", f"{label}: {value:.0f} {unit} — в пределах вашей нормы."

    direction = "above" if z > 0 else "below"
    delta = abs(value - baseline)
    if feature in LOWER_IS_CONCERNING and direction == "below":
        return direction, (
            f"{label} снижена: {value:.0f} {unit} против обычных {baseline:.0f}. "
            "Сниженная вариабельность часто сопровождает стресс, недосып или нагрузку."
        )
    if direction == "above":
        return direction, (
            f"{label} выше вашей нормы на {delta:.0f} {unit} "
            f"({value:.0f} против {baseline:.0f})."
        )
    return direction, (
        f"{label} ниже вашей нормы на {delta:.0f} {unit} "
        f"({value:.0f} против {baseline:.0f})."
    )


def score_window(
    features: dict[str, float],
    personal_baseline: Optional[dict[str, dict[str, float]]] = None,
) -> dict:
    """Score one feature window.

    `personal_baseline` (same shape as the artifact's population baseline) is
    preferred when the user has enough history: "high for you" is far more
    useful than "high for the average MIT-BIH subject".
    """
    artifact = _artifact()
    # Personal history beats a population figure; the healthy-adult reference is
    # the floor. The artifact's own MIT-BIH baseline is intentionally not used
    # for explanation — see HEALTHY_BASELINE above.
    baseline = personal_baseline or HEALTHY_BASELINE
    importances = (artifact or {}).get("importances") or {n: 1.0 for n in FEATURE_NAMES}

    # --- per-feature deviation -------------------------------------------
    contributions = []
    raw_weights = {}
    for name in FEATURE_NAMES:
        value = float(features[name])
        mean = float(baseline["mean"].get(name, HEALTHY_BASELINE["mean"][name]))
        std = float(baseline["std"].get(name, HEALTHY_BASELINE["std"][name])) or 1.0
        z = (value - mean) / std
        raw_weights[name] = abs(z) * float(importances.get(name, 1.0))
        direction, explanation = _describe(name, value, mean, z)
        contributions.append(
            {
                "feature": name,
                "label": FEATURE_LABELS[name],
                "value": round(value, 2),
                "baseline": round(mean, 2),
                "deviation": round(z, 2),
                "weight": 0.0,  # filled in below once the total is known
                "direction": direction,
                "explanation": explanation,
            }
        )

    total = sum(raw_weights.values()) or 1.0
    for item in contributions:
        item["weight"] = round(raw_weights[item["feature"]] / total, 3)
    contributions.sort(key=lambda c: -c["weight"])

    # --- model score ------------------------------------------------------
    predicted_label = None
    if artifact:
        vector = [to_vector(features)]
        scaled = artifact["scaler"].transform(vector)
        # score_samples is negative-oriented; map to 0..1 where 1 = most anomalous.
        raw = float(-artifact["isolation_forest"].score_samples(scaled)[0])
        score = max(0.0, min(1.0, (raw - 0.35) / 0.35))
        probability = float(artifact["classifier"].predict_proba(scaled)[0][1])
        # Blend: the supervised model is sharper where it has labels, the
        # unsupervised one generalises to rhythms it never saw.
        score = max(score, probability)
        # Threshold comes from training (max-F2 on held-out patients), not the
        # 0.5 default — see ml/train.py for why recall is favoured here.
        threshold = float(artifact.get("threshold", 0.5))
        predicted_label = "abnormal" if probability >= threshold else "normal"
    else:
        # No artifact: fall back to the largest normalised deviation.
        worst = max(abs(c["deviation"]) for c in contributions)
        score = max(0.0, min(1.0, (worst - 1.0) / 3.0))

    severity, rate_reason = _apply_rate_rules(float(features["mean_hr"]), _severity(score))

    return {
        "anomaly_score": round(score, 3),
        "severity": severity,
        "predicted_label": predicted_label,
        "rate_flag": rate_reason,
        "features": {k: round(float(v), 2) for k, v in features.items()},
        "contributions": contributions,
        "model_available": artifact is not None,
        "baseline_source": "personal" if personal_baseline else "healthy_population",
    }


def top_factors(contributions: list[dict], limit: int = 3) -> list[dict]:
    """The factors worth showing. Anything at normal deviation is noise."""
    meaningful = [c for c in contributions if c["direction"] != "normal"]
    return (meaningful or contributions)[:limit]
