from pathlib import Path
import json
import argparse
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'dataset' / 'processed' / 'movement_features.csv'
DEV_CSV = ROOT / 'dataset' / 'processed' / 'development_features.csv'
OUT = ROOT / 'backend' / 'ml' / 'saved_model' / 'readiness_model.joblib'
FEATURES = [
    'movement_quality','symmetry','rom','stability','landing_control',
    'movement_consistency','pain','psychological_readiness','recovery_trend'
]

parser = argparse.ArgumentParser(description='Train the return-to-play readiness model.')
parser.add_argument('--real-only', action='store_true', help='Require extracted real labelled video data; never use the synthetic development dataset.')
args = parser.parse_args()


def load_dataset(real_only=False):
    # Prefer the user's real extracted dataset. Development data is an explicit
    # fallback used only to keep the software demonstrable before athlete data exists.
    if CSV.exists():
        df = pd.read_csv(CSV).rename(columns={'pain_score': 'pain'})
        source = 'athlete_labeled_dataset'
        demo = False
    elif DEV_CSV.exists() and not real_only:
        df = pd.read_csv(DEV_CSV)
        source = 'synthetic_development_dataset'
        demo = True
    else:
        raise SystemExit('No extracted real dataset found. Add controlled labelled videos, run extract_dataset.py, then re-run with --real-only.')
    if 'recovery_trend' not in df.columns:
        df['recovery_trend'] = 50.0
    missing = [c for c in FEATURES + ['label'] if c not in df.columns]
    if missing:
        raise SystemExit(f'Missing dataset columns: {missing}')
    return df, source, demo


def main():
    df, source, demo = load_dataset(args.real_only)
    if df['label'].nunique() < 2:
        raise SystemExit('Need at least two label classes.')
    X = df[FEATURES].astype(float)
    y = df['label'].astype(str)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    pipe = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('model', RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            class_weight='balanced_subsample',
            min_samples_leaf=2,
            # One worker keeps training/prediction reliable on Windows,
            # restricted environments, and small deployment instances.
            n_jobs=1,
        )),
    ])
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    holdout_accuracy = float(accuracy_score(yte, pred))
    artifact = {
        'model': pipe,
        'metadata': {
            'version': 'research-2-dev' if demo else 'research-2',
            'demo': demo,
            'data_source': source,
            'feature_columns': FEATURES,
            'train_rows': int(len(Xtr)),
            'test_rows': int(len(Xte)),
            'holdout_accuracy': holdout_accuracy,
            'warning': 'Synthetic development dataset; not evidence of clinical performance.' if demo else 'Research prototype model; not clinically validated.',
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, OUT)
    print(json.dumps({k: v for k, v in artifact['metadata'].items() if k != 'warning'}, indent=2))
    print(f'Saved trained model: {OUT}')

if __name__ == '__main__':
    main()
