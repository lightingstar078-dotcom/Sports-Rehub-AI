from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, SyncQueue, Assessment, Athlete
from services.object_storage import upload as upload_cloud_video
import json, os, urllib.request
from pathlib import Path

router = APIRouter()
def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()

@router.get("/status")
def status(session: Session = Depends(db)):
    return {
        "pending": session.query(SyncQueue).filter(SyncQueue.status == "PENDING").count(),
        "synced": session.query(SyncQueue).filter(SyncQueue.status == "SYNCED").count(),
        "failed": session.query(SyncQueue).filter(SyncQueue.status == "FAILED").count()
    }

def _post_json(url, payload):
    req=urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r: return json.loads(r.read())

@router.post("/push")
def push(session: Session = Depends(db)):
    cloud=os.getenv("CLOUD_API_URL", "").strip().rstrip("/")
    pending=session.query(SyncQueue).filter(SyncQueue.status=="PENDING").all()
    if not cloud:
        return {"attempted":len(pending),"synced":0,"message":"Set CLOUD_API_URL in the local backend to enable local → Render synchronization."}
    import httpx
    synced=0; errors=[]
    for q in pending:
        try:
            payload=dict(q.payload or {})
            if q.entity_type=="assessment" and payload.get("video_path") and Path(payload["video_path"]).exists():
                with open(payload["video_path"],"rb") as vf:
                    up=httpx.post(cloud+"/api/sync/upload-video", files={"file":("assessment.mp4",vf,"video/mp4")}, timeout=180)
                up.raise_for_status()
                payload["video_path"]=up.json().get("key")
            resp=_post_json(cloud+"/api/sync/receive", {"entity_type":q.entity_type,"payload":payload})
            if resp.get("ok"):
                q.status="SYNCED"; synced += 1
                if q.entity_type=="assessment":
                    a=session.get(Assessment,q.entity_id)
                    if a: a.sync_status="SYNCED"
                session.commit()
            else: errors.append(resp.get("message","sync rejected"))
        except Exception as e:
            q.status="FAILED"; q.error_message=str(e); q.retry_count+=1; session.commit(); errors.append(str(e))
    return {"attempted":len(pending),"synced":synced,"errors":errors[:5]}

@router.post("/receive")
def receive(payload: dict, session: Session = Depends(db)):
    entity_type=payload.get("entity_type")
    data=payload.get("payload") or {}
    if entity_type=="athlete":
        from datetime import datetime
        obj=Athlete(id=int(data["id"]),name=data["name"],age=int(data["age"]),sport=data["sport"],injury=data["injury"],injury_side=data.get("injury_side","N/A"),created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow())
        session.merge(obj)
    elif entity_type=="assessment":
        from datetime import datetime
        obj=Assessment(id=int(data["id"]),athlete_id=int(data["athlete_id"]),date=datetime.fromisoformat(data["date"]) if data.get("date") else datetime.utcnow(),exercise=data["exercise"],movement_quality=float(data["movement_quality"]),symmetry=float(data["symmetry"]),rom=float(data["rom"]),stability=float(data["stability"]),landing_control=float(data.get("landing_control",0)),movement_consistency=float(data.get("movement_consistency",0)),pain=float(data["pain"]),psychological_readiness=float(data["psychological_readiness"]),readiness_score=float(data["readiness_score"]),status=data["status"],video_path=data.get("video_path"),original_size=int(data.get("original_size",0)),compressed_size=int(data.get("compressed_size",0)),video_duration=float(data.get("video_duration",0)),video_resolution=data.get("video_resolution","unknown"),analysis_json=data.get("analysis_json",{}),sync_status="SYNCED")
        session.merge(obj)
    else:
        raise HTTPException(400,"Unsupported sync entity")
    session.commit()
    return {"ok":True,"entity_type":entity_type,"id":data.get("id")}

@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    # Accept an already-compressed MP4 from the local node and store it in configured object storage / service storage.
    saved=await file.read()
    if not saved: raise HTTPException(400,"Empty video")
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False,suffix=".mp4") as f:
        f.write(saved); path=f.name
    try:
        key=upload_cloud_video(path)
        return {"ok":True,"key":key or Path(path).name}
    finally:
        Path(path).unlink(missing_ok=True)
