from pathlib import Path
import json
import argparse
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / 'dataset' / 'processed' / 'movement_features.csv'
DEV_CSV = ROOT / 'dataset' / 'processed' / 'development_features.csv'
MODEL = ROOT / 'backend' / 'ml' / 'saved_model' / 'readiness_model.joblib'
OUT = ROOT / 'dataset' / 'processed' / 'metrics.json'
FEATURES = ['movement_quality','symmetry','rom','stability','landing_control','movement_consistency','pain','psychological_readiness','recovery_trend']

parser = argparse.ArgumentParser(description='Evaluate the trained readiness model.')
parser.add_argument('--real-only', action='store_true', help='Require real extracted video data and a real-data model.')
args = parser.parse_args()

if not MODEL.exists():
    raise SystemExit('Model missing. Run train_model.py first.')

if CSV.exists():
    df = pd.read_csv(CSV).rename(columns={'pain_score': 'pain'})
    source = 'athlete_labeled_dataset'
elif DEV_CSV.exists() and not args.real_only:
    df = pd.read_csv(DEV_CSV)
    source = 'synthetic_development_dataset'
else:
    raise SystemExit('No extracted real video dataset found. Add real videos and labels, then run extract_dataset.py.')

if 'recovery_trend' not in df.columns:
    df['recovery_trend'] = 50.0
X = df[FEATURES].astype(float)
y = df.label.astype(str)
_, Xte, _, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
artifact = joblib.load(MODEL)
m = artifact['model'] if isinstance(artifact, dict) else artifact
metadata = artifact.get('metadata', {}) if isinstance(artifact, dict) else {}
if args.real_only and metadata.get('demo', True):
    raise SystemExit('The installed model was trained on synthetic development data. Train with train_model.py --real-only before real-only evaluation.')
yp = m.predict(Xte)
p, r, f, _ = precision_recall_fscore_support(yte, yp, average='weighted', zero_division=0)
labels = sorted(y.unique())
metrics = {
    'accuracy': float(accuracy_score(yte, yp)),
    'precision_weighted': float(p),
    'recall_weighted': float(r),
    'f1_weighted': float(f),
    'labels': labels,
    'confusion_matrix': confusion_matrix(yte, yp, labels=labels).tolist(),
    'data_source': source,
    'demo_model': bool(metadata.get('demo', False)),
    'warning': metadata.get('warning'),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
print(json.dumps(metrics, indent=2))
