"""Synthetic heart-rate stream, used until the hardware sensor is attached.

This is not random noise dressed up as data. It models the three things that
actually shape a resting adult's pulse over a day, so the anomaly model sees a
realistic signal and the demo is honest about what it is:

1. Circadian rhythm — pulse dips overnight and peaks in the early afternoon.
2. Activity state — rest / light / active, moving as a small Markov chain, with
   the pulse easing toward the target rather than teleporting to it.
3. Beat-to-beat variability — real HRV plus sensor noise.

Scenarios inject the patterns we want to demonstrate (tachycardia, atrial
fibrillation). They are labelled as simulated end-to-end: every reading is
stored with source="simulated" and the UI shows a demo badge. Nothing here is
ever presented as a real measurement.

Swap to hardware by setting HR_SOURCE=device: the API contract is unchanged, the
device just POSTs to /api/heart-rate instead of this generator filling the gap.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

# target_delta (bpm above resting), mean dwell time in samples, HRV multiplier
ACTIVITY_STATES = {
    "rest": {"delta": 0.0, "hrv": 1.0},
    "light": {"delta": 14.0, "hrv": 0.8},
    "active": {"delta": 32.0, "hrv": 0.6},
}

# Row i -> probability of moving to each state. Elderly users spend most of the
# day at rest, so the chain is deliberately sticky there.
TRANSITIONS = {
    "rest": [("rest", 0.94), ("light", 0.06), ("active", 0.0)],
    "light": [("rest", 0.20), ("light", 0.75), ("active", 0.05)],
    "active": [("rest", 0.05), ("light", 0.35), ("active", 0.60)],
}

SCENARIOS = {
    "normal": "Обычный ритм",
    "tachycardia": "Тахикардия: устойчиво высокий пульс",
    "afib": "Мерцательная аритмия: нерегулярный ритм, высокая вариабельность",
    "bradycardia": "Брадикардия: пульс ниже нормы",
}


@dataclass
class _UserState:
    resting_hr: float = 68.0
    current_hr: float = 68.0
    activity: str = "rest"
    scenario: str = "normal"
    rng: random.Random = field(default_factory=random.Random)


_states: dict[str, _UserState] = {}


def _circadian_offset(now: datetime) -> float:
    """Pulse relative to daily mean: trough ~04:00, peak ~15:00."""
    hours = now.hour + now.minute / 60.0
    return -6.0 * math.cos((hours - 15.0) / 24.0 * 2 * math.pi)


def _state_for(user_id: str, resting_hr: Optional[float] = None) -> _UserState:
    state = _states.get(user_id)
    if state is None:
        # Seed per user so a given account's stream is reproducible across restarts.
        state = _UserState(rng=random.Random(hash(user_id) & 0xFFFFFFFF))
        state.resting_hr = resting_hr or 68.0
        state.current_hr = state.resting_hr
        _states[user_id] = state
    if resting_hr and state.resting_hr != resting_hr:
        state.resting_hr = resting_hr
    return state


def set_scenario(user_id: str, scenario: str) -> str:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    _state_for(user_id).scenario = scenario
    return scenario


def get_scenario(user_id: str) -> str:
    return _state_for(user_id).scenario


def _step_activity(state: _UserState) -> None:
    roll = state.rng.random()
    cumulative = 0.0
    for name, probability in TRANSITIONS[state.activity]:
        cumulative += probability
        if roll <= cumulative:
            state.activity = name
            return


def next_reading(user_id: str, resting_hr: Optional[float] = None, now: Optional[datetime] = None) -> dict:
    """Produce the next simulated sample for this user."""
    now = now or datetime.now(timezone.utc)
    state = _state_for(user_id, resting_hr)
    rng = state.rng

    _step_activity(state)
    activity = ACTIVITY_STATES[state.activity]

    target = state.resting_hr + activity["delta"] + _circadian_offset(now)
    hrv_scale = activity["hrv"]

    if state.scenario == "tachycardia":
        target += 42.0
        hrv_scale *= 0.5
    elif state.scenario == "bradycardia":
        target -= 22.0
    elif state.scenario == "afib":
        # AFib's signature is irregularity, not just rate: large beat-to-beat
        # swings on a modestly raised mean.
        target += 16.0
        hrv_scale *= 4.5

    # Ease toward the target instead of jumping — the heart has inertia.
    state.current_hr += (target - state.current_hr) * 0.25
    sample = state.current_hr + rng.gauss(0, 1.8 * hrv_scale)

    if state.scenario == "afib" and rng.random() < 0.30:
        sample += rng.choice([-1, 1]) * rng.uniform(8, 22)

    sample = max(35.0, min(190.0, sample))

    return {
        "bpm": round(sample, 1),
        "source": "simulated",
        "context": state.activity,
        "measured_at": now,
    }


def reset(user_id: str) -> None:
    _states.pop(user_id, None)
