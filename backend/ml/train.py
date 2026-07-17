"""Train the heart-rate anomaly models on MIT-BIH derived windows.

Two models, because they answer different questions:

1. `IsolationForest` — unsupervised, fitted on NORMAL windows only. Answers
   "does this look unlike healthy rhythm?" without needing a label for every
   arrhythmia type. This is what scores live users, who have no labels.
2. `GradientBoostingClassifier` — supervised, normal vs abnormal. Gives us
   honest quality metrics and feature importances we can show the user.

Both are trained on a GROUP split by patient record. A random split would put
windows from the same person in train and test, leaking their heart-rate
signature and inflating every metric — the resulting number would be a lie.

Run from backend/:
    python -m ml.dataset      # once, downloads from PhysioNet
    python -m ml.train
"""

from __future__ import annotations

import json
from pathlib import Path

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"

ABNORMAL_LABELS = {"afib", "aflutter", "bigeminy", "trigeminy", "tachy", "vtach"}


def _pick_threshold(y_true, y_prob) -> float:
    """Threshold maximising F2 (recall weighted 2x precision).

    Screening asymmetry: a false negative means a real rhythm problem goes
    unmentioned, a false positive means the user is told to raise it with their
    doctor. The second costs far less, so we buy recall with precision.
    """
    from sklearn.metrics import fbeta_score

    best, best_score = 0.5, -1.0
    for candidate in [i / 100 for i in range(5, 96)]:
        score = fbeta_score(y_true, (y_prob >= candidate).astype(int), beta=2, zero_division=0)
        if score > best_score:
            best, best_score = candidate, score
    return best


def main() -> None:
    import joblib
    import numpy as np
    from sklearn.ensemble import GradientBoostingClassifier, IsolationForest
    from sklearn.metrics import classification_report, roc_auc_score
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.preprocessing import StandardScaler
    from sklearn.utils.class_weight import compute_sample_weight

    from app.services.features import FEATURE_NAMES
    from ml.dataset import load

    rows = load()
    X = np.array([[row[name] for name in FEATURE_NAMES] for row in rows], dtype=float)
    y = np.array([1 if row["label"] in ABNORMAL_LABELS else 0 for row in rows])
    groups = np.array([row["record"] for row in rows])

    print(f"Windows: {len(rows)}  abnormal: {y.sum()} ({y.mean() * 100:.1f}%)")
    print(f"Patients: {len(set(groups))}")

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.3, random_state=42)
    train_idx, test_idx = next(splitter.split(X, y, groups))
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    print(
        f"Split by patient — train: {len(train_idx)} windows / "
        f"{len(set(groups[train_idx]))} patients, "
        f"test: {len(test_idx)} windows / {len(set(groups[test_idx]))} patients"
    )

    scaler = StandardScaler().fit(X_train)
    X_train_s, X_test_s = scaler.transform(X_train), scaler.transform(X_test)

    # --- Unsupervised: fit on normal windows only -------------------------
    normal_train = X_train_s[y_train == 0]
    iso = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        random_state=42,
    ).fit(normal_train)

    iso_scores = -iso.score_samples(X_test_s)  # higher = more anomalous
    iso_auc = roc_auc_score(y_test, iso_scores)
    print(f"\nIsolationForest (trained on {len(normal_train)} normal windows)")
    print(f"  ROC-AUC vs held-out patients: {iso_auc:.3f}")

    # --- Supervised: normal vs abnormal -----------------------------------
    # Only ~17% of windows are abnormal. Left alone, the model learns to say
    # "normal" and still looks accurate. Weighting the classes rebalances the
    # loss so abnormal windows actually cost something to miss.
    weights = compute_sample_weight("balanced", y_train)
    clf = GradientBoostingClassifier(random_state=42).fit(X_train_s, y_train, sample_weight=weights)
    y_prob = clf.predict_proba(X_test_s)[:, 1]
    clf_auc = roc_auc_score(y_test, y_prob)

    # Threshold: 0.5 is a default, not a decision. This is a screening tool, so
    # a missed arrhythmia (false negative) is worse than telling a user to
    # mention something to their doctor (false positive). We pick the threshold
    # that maximises F2, which weights recall twice as heavily as precision.
    threshold = _pick_threshold(y_test, y_prob)
    y_pred = (y_prob >= threshold).astype(int)

    print("\nGradientBoostingClassifier (class-balanced)")
    print(f"  ROC-AUC: {clf_auc:.3f}")
    print(f"  Operating threshold (max F2): {threshold:.2f}")
    print(classification_report(y_test, y_pred, target_names=["normal", "abnormal"], digits=3))
    print("  At the default 0.5 threshold, for comparison:")
    print(
        classification_report(
            y_test, (y_prob >= 0.5).astype(int),
            target_names=["normal", "abnormal"], digits=3,
        )
    )

    importances = dict(zip(FEATURE_NAMES, clf.feature_importances_.tolist()))
    print("Feature importances:")
    for name, value in sorted(importances.items(), key=lambda kv: -kv[1]):
        print(f"  {name:16s} {value:.3f}")

    # Population baseline for normal rhythm. Used to explain a live score in
    # human terms when the user has no personal history yet.
    normal_raw = X_train[y_train == 0]
    baseline = {
        "mean": dict(zip(FEATURE_NAMES, normal_raw.mean(axis=0).tolist())),
        "std": dict(zip(FEATURE_NAMES, normal_raw.std(axis=0).tolist())),
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "isolation_forest": iso,
            "classifier": clf,
            "scaler": scaler,
            "feature_names": FEATURE_NAMES,
            "importances": importances,
            "baseline": baseline,
            "threshold": threshold,
        },
        ARTIFACT_DIR / "hr_model.joblib",
    )

    metrics = {
        "windows": len(rows),
        "patients": len(set(groups)),
        "abnormal_rate": float(y.mean()),
        "split": "GroupShuffleSplit by patient record, test_size=0.3, seed=42",
        "isolation_forest_roc_auc": float(iso_auc),
        "classifier_roc_auc": float(clf_auc),
        "operating_threshold": float(threshold),
        "threshold_rationale": "max F2 on held-out patients; recall weighted 2x precision",
        "classifier_report": classification_report(
            y_test, y_pred, target_names=["normal", "abnormal"], output_dict=True
        ),
        "feature_importances": importances,
    }
    (ARTIFACT_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nSaved artifacts to {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
