from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, Athlete, SyncQueue
from schemas import AthleteCreate

router = APIRouter()
def db():
    s = SessionLocal()
    try: yield s
    finally: s.close()

@router.get("")
def list_athletes(session: Session = Depends(db)):
    return [serialize(a) for a in session.query(Athlete).order_by(Athlete.id.desc()).all()]

@router.get("/{athlete_id}")
def get_athlete(athlete_id: int, session: Session = Depends(db)):
    a = session.get(Athlete, athlete_id)
    if not a: raise HTTPException(404, "Athlete not found")
    return serialize(a)

@router.post("")
def create_athlete(payload: AthleteCreate, session: Session = Depends(db)):
    a = Athlete(**payload.model_dump())
    session.add(a); session.commit(); session.refresh(a)
    session.add(SyncQueue(entity_type="athlete", entity_id=a.id, operation="CREATE", payload=serialize(a), status="PENDING"))
    session.commit()
    return serialize(a)

def serialize(a):
    return {"id":a.id,"name":a.name,"age":a.age,"sport":a.sport,"injury":a.injury,"injury_side":a.injury_side,"created_at":a.created_at.isoformat()}
