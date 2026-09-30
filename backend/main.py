from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os

from database import init_db
from routes.athletes import router as athletes_router
from routes.assessment import router as assessment_router
from routes.vision import router as vision_router
from routes.ml import router as ml_router
from routes.chat import router as chat_router
from routes.sync import router as sync_router
from services.system_service import system_status

BASE = Path(__file__).resolve().parent
(Path(os.getenv("STORAGE_DIR", BASE / "storage")) / "videos").mkdir(parents=True, exist_ok=True)
(BASE / "ml" / "saved_model").mkdir(parents=True, exist_ok=True)
(BASE / "models").mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Sports Rehab AI", version="1.0.0", description="Offline-first return-to-play readiness screening prototype", lifespan=lifespan)

origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "*").split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "sports-rehab-ai", **system_status()}

@app.get("/api/system/status")
def status():
    return system_status()

app.include_router(athletes_router, prefix="/api/athletes", tags=["athletes"])
app.include_router(assessment_router, prefix="/api/assessment", tags=["assessment"])
app.include_router(vision_router, prefix="/api/vision", tags=["vision"])
app.include_router(ml_router, prefix="/api/ml", tags=["ml"])
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(sync_router, prefix="/api/sync", tags=["sync"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
