import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

def test_ml_status():
    r = client.get('/api/ml/status')
    assert r.status_code == 200
    assert 'available' in r.json()

def test_trained_model_prediction():
    payload = {
        'movement_quality': 80, 'symmetry': 80, 'rom': 80, 'stability': 80,
        'landing_control': 80, 'movement_consistency': 80, 'pain': 2,
        'psychological_readiness': 80, 'recovery_trend': 70,
    }
    r = client.post('/api/ml/predict', json=payload)
    assert r.status_code == 200
    assert r.json()['model_available'] is True
    assert r.json()['status'] in {'GREEN', 'YELLOW', 'RED'}

def test_local_assistant_uses_assessment_data():
    assessment = {'readiness_score': 61, 'status': 'YELLOW', 'pain': 5, 'symmetry': 64, 'rom': 67, 'stability': 75}
    r = client.post('/api/chat', json={'message': 'Why is my readiness score low?', 'assessment': assessment, 'online': False})
    assert r.status_code == 200
    assert '61/100' in r.json()['reply']
    assert r.json()['assistant_type'] == 'local assessment-aware recovery support'
