"""Train/evaluate a research-only ACL-history model with participant CV."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "dataset" / "external" / "acl_jump_landing" / "derived" / "acl_jump_trials.csv"
MODEL = DATA.parent / "acl_history_research_model.joblib"
REPORT = DATA.parent / "acl_history_cv_results.json"
LABELS = ["CONTROL", "ACL_HISTORY"]


def _new_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("classifier", RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=1,
        )),
    ])


def _metrics(y_true, y_pred) -> dict:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "labels_order": LABELS,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
    }


def main() -> None:
    if not DATA.exists():
        raise SystemExit(f"Missing {DATA}. Run ml_training/extract_acl_history_dataset.py first.")
    frame = pd.read_csv(DATA)
    features = sorted(column for column in frame if column.startswith("joint_") and
                      column.rsplit("_", 1)[-1] in {"mean", "std", "range"})
    required = {"participant_id", "label", *features}
    missing = required.difference(frame.columns)
    if missing or not features:
        raise SystemExit(f"Converted dataset is missing required fields: {sorted(missing)}")
    frame = frame[frame["label"].isin(LABELS)].copy()
    frame[features] = frame[features].replace([np.inf, -np.inf], np.nan)
    if frame["label"].nunique() != 2:
        raise SystemExit("Both CONTROL and ACL_HISTORY classes are required.")
    per_person = frame.groupby("participant_id")["label"].nunique()
    if (per_person != 1).any():
        raise SystemExit("A participant has conflicting labels; refusing a potentially leaky evaluation.")
    groups = frame["participant_id"].to_numpy()
    y = frame["label"].to_numpy()
    X = frame[features].astype(float)
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    oof_probability = np.full((len(frame), len(LABELS)), np.nan, dtype=float)
    fold_details = []
    for fold, (train_idx, test_idx) in enumerate(splitter.split(X, y, groups), start=1):
        model = _new_model()
        model.fit(X.iloc[train_idx], y[train_idx])
        probabilities = model.predict_proba(X.iloc[test_idx])
        for class_index, label in enumerate(model.classes_):
            oof_probability[test_idx, LABELS.index(label)] = probabilities[:, class_index]
        fold_details.append({
            "fold": fold,
            "train_participants": int(len(set(groups[train_idx]))),
            "test_participants": int(len(set(groups[test_idx]))),
            "train_trials": int(len(train_idx)),
            "test_trials": int(len(test_idx)),
        })
    if np.isnan(oof_probability).any():
        raise SystemExit("Cross-validation did not produce predictions for every row.")
    row_pred = np.asarray(LABELS)[np.argmax(oof_probability, axis=1)]
    cv_rows = _metrics(y, row_pred)
    predictions = frame[["participant_id", "label"]].copy()
    predictions["p_control"] = oof_probability[:, 0]
    predictions["p_acl_history"] = oof_probability[:, 1]
    person_predictions = predictions.groupby("participant_id", as_index=False).agg(
        label=("label", "first"),
        p_control=("p_control", "mean"),
        p_acl_history=("p_acl_history", "mean"),
        trials=("label", "size"),
    )
    person_pred = np.asarray(LABELS)[np.argmax(person_predictions[["p_control", "p_acl_history"]].to_numpy(), axis=1)]
    cv_participants = _metrics(person_predictions["label"], person_pred)
    cv_participants["participant_count"] = int(len(person_predictions))
    cv_participants["trials_per_participant_min"] = int(person_predictions["trials"].min())
    cv_participants["trials_per_participant_max"] = int(person_predictions["trials"].max())

    final_model = _new_model()
    final_model.fit(X, y)
    metadata = {
        "model_scope": "acl_history_research_only",
        "target": "ACL history vs control group",
        "data_source": "Calisti et al. 2025 Figshare CC BY 4.0 dataset",
        "feature_window": "first 101 samples from knee initial contact, per joint channel; mean/std/range",
        "validation": "5-fold StratifiedGroupKFold; participant IDs held out by fold",
        "trial_count": int(len(frame)),
        "participant_count": int(frame["participant_id"].nunique()),
        "class_trial_counts": {str(k): int(v) for k, v in frame["label"].value_counts().items()},
        "class_participant_counts": {str(k): int(v) for k, v in frame[["participant_id", "label"]].drop_duplicates()["label"].value_counts().items()},
        "feature_count": int(len(features)),
        "folds": fold_details,
        "cross_validation_trial_metrics": cv_rows,
        "cross_validation_participant_metrics": cv_participants,
        "limitation": "Research dataset classification only; not return-to-play readiness, re-injury risk, diagnosis, or clinical validation.",
    }
    MODEL.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": final_model, "metadata": metadata, "feature_columns": features}, MODEL)
    REPORT.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    print(f"Saved research-only model: {MODEL}")
    print(f"Saved group-held-out evaluation: {REPORT}")


if __name__ == "__main__":
    main()
