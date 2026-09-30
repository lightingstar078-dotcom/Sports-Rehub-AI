import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import Athlete, Assessment, PsychologicalResponse, SessionLocal, SyncQueue
from ml.model_service import predict
from ml.readiness import guidance
from routes.vision import analyze_video
from services.object_storage import upload as upload_cloud_video

router = APIRouter()

def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@router.post('')
async def create_assessment(
    athlete_id: int = Form(...), exercise: str = Form(...), pain: float = Form(...),
    psychological_readiness: float = Form(...), psychology_json: str = Form('[]'),
    # Kept for backward compatibility; the server calculates it from history.
    recovery_trend: float = Form(50), file: UploadFile = File(...), session: Session = Depends(db),
):
    if exercise not in {'squat', 'single_leg_hop', 'single_leg_balance'}:
        raise HTTPException(422, 'Unsupported exercise')
    if not 0 <= pain <= 10:
        raise HTTPException(422, 'Pain must be 0-10')
    if not 0 <= psychological_readiness <= 100:
        raise HTTPException(422, 'Psychological readiness must be 0-100')
    if athlete_id <= 0 or not session.get(Athlete, athlete_id):
        raise HTTPException(404, 'Athlete not found')
    try:
        responses = json.loads(psychology_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(422, 'Psychology responses must be valid JSON.') from exc
    if not isinstance(responses, list) or any(not isinstance(item, dict) or not 1 <= int(item.get('response', 0)) <= 5 for item in responses):
        raise HTTPException(422, 'Psychology responses must be a list of answers from 1 to 5.')

    result = await analyze_video(file, exercise)
    try:
        cloud_video_key = upload_cloud_video(result['path'])
    except Exception:
        # A configured-but-unavailable object store must not discard a valid local result.
        cloud_video_key = None
    features = result['features']
    previous = session.query(Assessment).filter(Assessment.athlete_id == athlete_id).order_by(Assessment.date.desc()).limit(2).all()
    if previous:
        recovery_trend = max(0, min(100, sum(item.readiness_score for item in previous) / len(previous)))
    ml = predict({**features, 'pain': pain, 'psychological_readiness': psychological_readiness, 'recovery_trend': recovery_trend})
    status, score = ml.get('status'), ml.get('readiness_score')
    if score is None:
        raise HTTPException(409, 'Assessment was analyzed, but no trained ML model is installed. Train a model before generating readiness scores.')

    assessment = Assessment(
        athlete_id=athlete_id, exercise=exercise, movement_quality=features['movement_quality'], symmetry=features['symmetry'], rom=features['rom'], stability=features['stability'],
        landing_control=features['landing_control'], movement_consistency=features['movement_consistency'], pain=pain, psychological_readiness=psychological_readiness,
        readiness_score=score, status=status, video_path=cloud_video_key or result['path'], original_size=result['original_size'], compressed_size=result['compressed_size'],
        video_duration=result['metadata']['duration'], video_resolution=result['metadata']['resolution'],
        analysis_json={'features': features, 'ml': ml, 'guidance': guidance(status, score), 'cloud_video_key': cloud_video_key}, sync_status='PENDING',
    )
    session.add(assessment); session.commit(); session.refresh(assessment)
    for response in responses:
        session.add(PsychologicalResponse(assessment_id=assessment.id, question=str(response.get('question', '')), response=int(response['response'])))
    session.add(SyncQueue(entity_type='assessment', entity_id=assessment.id, operation='CREATE', payload=serialize(assessment), status='PENDING'))
    session.commit()
    return serialize(assessment)

@router.get('')
def list_assessments(athlete_id: int | None = None, session: Session = Depends(db)):
    query = session.query(Assessment).order_by(Assessment.date.desc())
    if athlete_id:
        query = query.filter(Assessment.athlete_id == athlete_id)
    return [serialize(assessment) for assessment in query.all()]

@router.get('/{assessment_id}')
def get_assessment(assessment_id: int, session: Session = Depends(db)):
    assessment = session.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(404, 'Assessment not found')
    return serialize(assessment)

def serialize(assessment: Assessment):
    return {
        'id': assessment.id, 'athlete_id': assessment.athlete_id, 'exercise': assessment.exercise, 'date': assessment.date.isoformat(),
        'movement_quality': assessment.movement_quality, 'symmetry': assessment.symmetry, 'rom': assessment.rom, 'stability': assessment.stability,
        'landing_control': assessment.landing_control, 'movement_consistency': assessment.movement_consistency, 'pain': assessment.pain,
        'psychological_readiness': assessment.psychological_readiness, 'readiness_score': assessment.readiness_score, 'status': assessment.status,
        'video_path': assessment.video_path, 'original_size': assessment.original_size, 'compressed_size': assessment.compressed_size,
        'video_duration': assessment.video_duration, 'video_resolution': assessment.video_resolution, 'analysis_json': assessment.analysis_json, 'sync_status': assessment.sync_status,
    }
