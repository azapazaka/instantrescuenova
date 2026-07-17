"""Heart-rate window features.

Shared by offline training (ml/train.py) and online scoring
(app/services/anomaly.py). Keeping one implementation is what stops the classic
train/serve skew bug where the model is fed differently-shaped features at
inference time than it saw during training.

Features are derived from a sequence of RR intervals (ms). When the input is a
BPM series instead, RR is reconstructed as 60000/bpm — an approximation that is
adequate for trend/variability features but not for beat-level arrhythmia work.
That limitation is documented in the README.
"""

from __future__ import annotations

import math
from typing import Optional

# Order matters: this is the model's input vector layout.
FEATURE_NAMES = [
    "mean_hr",
    "min_hr",
    "max_hr",
    "sdnn",
    "rmssd",
    "pnn50",
    "hr_range",
    "hr_trend_slope",
]

FEATURE_LABELS = {
    "mean_hr": "Средний пульс",
    "min_hr": "Минимальный пульс",
    "max_hr": "Максимальный пульс",
    "sdnn": "Вариабельность ритма (SDNN)",
    "rmssd": "Краткосрочная вариабельность (RMSSD)",
    "pnn50": "Доля неровных интервалов (pNN50)",
    "hr_range": "Разброс пульса",
    "hr_trend_slope": "Тренд пульса за окно",
}

FEATURE_UNITS = {
    "mean_hr": "уд/мин",
    "min_hr": "уд/мин",
    "max_hr": "уд/мин",
    "sdnn": "мс",
    "rmssd": "мс",
    "pnn50": "%",
    "hr_range": "уд/мин",
    "hr_trend_slope": "уд/мин за окно",
}


def bpm_to_rr(bpm_values: list[float]) -> list[float]:
    """Convert BPM samples to approximate RR intervals in ms."""
    return [60000.0 / bpm for bpm in bpm_values if bpm and bpm > 0]


def rr_to_bpm(rr_values: list[float]) -> list[float]:
    return [60000.0 / rr for rr in rr_values if rr and rr > 0]


def _slope(values: list[float]) -> float:
    """Least-squares slope over evenly spaced samples, in units per window."""
    n = len(values)
    if n < 2:
        return 0.0
    mean_x = (n - 1) / 2
    mean_y = sum(values) / n
    numerator = sum((i - mean_x) * (v - mean_y) for i, v in enumerate(values))
    denominator = sum((i - mean_x) ** 2 for i in range(n))
    if denominator == 0:
        return 0.0
    return (numerator / denominator) * (n - 1)


def _std(values: list[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


def extract_features(rr_intervals: list[float]) -> Optional[dict[str, float]]:
    """Compute one feature vector from RR intervals (ms).

    Returns None when the window is too short to produce stable variability
    statistics — a partial window is worse than no window, because it produces
    confident-looking garbage.
    """
    rr = [v for v in rr_intervals if v and 250 <= v <= 3000]  # physiological plausibility
    if len(rr) < 10:
        return None

    hr = rr_to_bpm(rr)
    successive_diffs = [abs(rr[i + 1] - rr[i]) for i in range(len(rr) - 1)]
    nn50 = sum(1 for d in successive_diffs if d > 50)

    return {
        "mean_hr": sum(hr) / len(hr),
        "min_hr": min(hr),
        "max_hr": max(hr),
        "sdnn": _std(rr),
        "rmssd": math.sqrt(sum(d**2 for d in successive_diffs) / len(successive_diffs))
        if successive_diffs
        else 0.0,
        "pnn50": (nn50 / len(successive_diffs) * 100) if successive_diffs else 0.0,
        "hr_range": max(hr) - min(hr),
        "hr_trend_slope": _slope(hr),
    }


def to_vector(features: dict[str, float]) -> list[float]:
    return [features[name] for name in FEATURE_NAMES]
