"""Build a labelled heart-rate window dataset from the MIT-BIH Arrhythmia Database.

Source
------
MIT-BIH Arrhythmia Database v1.0.0 (PhysioNet), 48 half-hour two-channel
ambulatory ECG recordings from 47 subjects, sampled at 360 Hz, with
beat-by-beat cardiologist annotations.
    https://physionet.org/content/mitdb/1.0.0/
    Moody GB, Mark RG. IEEE Eng in Med and Biol 20(3):45-50 (2001).
    PhysioNet is distributed under the ODC-BY 1.0 licence.

What we take from it
--------------------
We do NOT use the raw ECG waveform. We use the *beat annotations* only, and
derive the RR interval series (time between consecutive heartbeats). RR is what
a consumer pulse sensor can actually produce, so a model trained on it transfers
to the hardware we plan to attach — a model trained on 360 Hz ECG morphology
would not.

Rhythm labels come from the `aux_note` field, which marks rhythm changes such as
`(N` (normal sinus), `(AFIB` (atrial fibrillation), `(B` (bigeminy). A label
applies from its annotation until the next rhythm marker.

Limitations (documented in the README)
--------------------------------------
- MIT-BIH subjects are not specifically elderly; age/sex metadata is coarse.
- The database is deliberately arrhythmia-rich, so class balance does not
  reflect a general population's prevalence.
- RR derived from expert annotations is cleaner than RR from an optical wrist
  sensor. Real device noise is simulated separately, not learned from here.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
OUT_PATH = DATA_DIR / "windows.jsonl"

# Rhythm annotations we keep. Everything else collapses into "other".
RHYTHM_MAP = {
    "(N": "normal",
    "(AFIB": "afib",
    "(AFL": "aflutter",
    "(B": "bigeminy",
    "(T": "trigeminy",
    "(SVTA": "tachy",
    "(VT": "vtach",
}

WINDOW_BEATS = 128  # ~2 min at 60 bpm; long enough for stable SDNN/RMSSD
WINDOW_STRIDE = 64  # 50% overlap for more training windows


def _rhythm_spans(annotation) -> list[tuple[int, str]]:
    """Return (sample_index, rhythm_label) at each rhythm change."""
    spans: list[tuple[int, str]] = []
    for sample, note in zip(annotation.sample, annotation.aux_note):
        note = (note or "").strip("\x00").strip()
        if note.startswith("("):
            spans.append((int(sample), RHYTHM_MAP.get(note, "other")))
    return spans


def _rhythm_at(spans: list[tuple[int, str]], sample: int) -> str:
    label = "unknown"
    for start, name in spans:
        if start <= sample:
            label = name
        else:
            break
    return label


def build(records: list[str] | None = None) -> Path:
    import wfdb

    from app.services.features import extract_features

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    records = records or wfdb.get_record_list("mitdb")

    rows: list[dict] = []
    label_counts: Counter[str] = Counter()

    for record_name in records:
        try:
            annotation = wfdb.rdann(record_name, "atr", pn_dir="mitdb")
        except Exception as exc:  # network or missing record
            print(f"  skip {record_name}: {exc}")
            continue

        fs = annotation.fs or 360
        # 'N','L','R','e','j','A','a','J','S','V','E','F','/','f','Q' are beats;
        # non-beat markers (rhythm, noise) must not enter the RR series.
        beat_symbols = set("NLRejAaJSVEF/fQ")
        beats = [
            int(sample)
            for sample, symbol in zip(annotation.sample, annotation.symbol)
            if symbol in beat_symbols
        ]
        if len(beats) < WINDOW_BEATS + 1:
            continue

        spans = _rhythm_spans(annotation)

        for start in range(0, len(beats) - WINDOW_BEATS, WINDOW_STRIDE):
            window = beats[start : start + WINDOW_BEATS + 1]
            rr = [(window[i + 1] - window[i]) / fs * 1000.0 for i in range(len(window) - 1)]
            features = extract_features(rr)
            if features is None:
                continue

            # A window spanning a rhythm change is ambiguous; label by its middle
            # beat and drop it if the rhythm is not one we recognise.
            label = _rhythm_at(spans, window[len(window) // 2])
            if label == "unknown":
                continue

            rows.append({"record": record_name, "label": label, **features})
            label_counts[label] += 1

        print(f"  {record_name}: {label_counts.total()} windows so far")

    with OUT_PATH.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"\nWrote {len(rows)} windows to {OUT_PATH}")
    print("Label distribution:")
    for label, count in label_counts.most_common():
        print(f"  {label:10s} {count:6d}  ({count / len(rows) * 100:.1f}%)")
    return OUT_PATH


def load() -> list[dict]:
    if not OUT_PATH.exists():
        raise FileNotFoundError(
            f"{OUT_PATH} not found. Run `python -m ml.dataset` from backend/ first."
        )
    with OUT_PATH.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", nargs="*", help="Subset of MIT-BIH record ids")
    args = parser.parse_args()
    build(args.records)
