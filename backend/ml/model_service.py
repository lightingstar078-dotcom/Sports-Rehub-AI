from functools import lru_cache
from pathlib import Path
import os

import joblib

MODEL_PATH = Path(os.getenv('ML_MODEL_PATH', Path(__file__).resolve().parent / 'saved_model' / 'readiness_model.joblib'))
FEATURES = ['movement_quality', 'symmetry', 'rom', 'stability', 'landing_control', 'movement_consistency', 'pain', 'psychological_readiness', 'recovery_trend']

@lru_cache(maxsize=1)
def _artifact():
    return joblib.load(MODEL_PATH)

def model_status():
    status = {'available': MODEL_PATH.exists(), 'path': str(MODEL_PATH), 'features': FEATURES}
    if not MODEL_PATH.exists():
        return status
    try:
        artifact = _artifact()
        status['metadata'] = artifact.get('metadata', {}) if isinstance(artifact, dict) else {}
    except Exception as exc:
        status.update({'available': False, 'error': f'Model could not be loaded: {exc}'})
    return status

def predict(features: dict):
    missing = [name for name in FEATURES if name not in features]
    if missing:
        return {'model_available': False, 'message': f'Missing model features: {", ".join(missing)}', 'status': None, 'probability': None, 'readiness_score': None}
    if not MODEL_PATH.exists():
        return {'model_available': False, 'message': 'No trained readiness model is installed. Train one with ml_training/train_model.py.', 'status': None, 'probability': None, 'readiness_score': None}
    try:
        artifact = _artifact()
        model = artifact['model'] if isinstance(artifact, dict) and 'model' in artifact else artifact
        metadata = artifact.get('metadata', {}) if isinstance(artifact, dict) else {}
        import pandas as pd
        frame = pd.DataFrame([[float(features[name]) for name in FEATURES]], columns=FEATURES)
        label = str(model.predict(frame)[0])
        probabilities = model.predict_proba(frame)[0] if hasattr(model, 'predict_proba') else None
    except Exception as exc:
        return {'model_available': False, 'message': f'Model prediction failed: {exc}', 'status': None, 'probability': None, 'readiness_score': None}

    classes = list(getattr(model, 'classes_', []))
    probability = float(max(probabilities)) if probabilities is not None and len(probabilities) else None
    anchors = {'RED': 30.0, 'YELLOW': 62.0, 'GREEN': 85.0}
    score = anchors.get(label, 50.0)
    if probabilities is not None and classes:
        score = sum(float(value) * anchors.get(str(class_name), 50.0) for class_name, value in zip(classes, probabilities))
    return {
        'model_available': True, 'status': label, 'probability': round(probability, 3) if probability is not None else None,
        'readiness_score': round(score, 1), 'demo_model': bool(metadata.get('demo', False)), 'model_version': metadata.get('version', 'research'),
        'data_source': metadata.get('data_source', 'unknown'), 'model_warning': metadata.get('warning'),
    }
