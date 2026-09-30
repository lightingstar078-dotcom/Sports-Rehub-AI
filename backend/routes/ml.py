from fastapi import APIRouter
from schemas import MLPredictRequest
from ml.model_service import model_status, predict

router = APIRouter()

@router.get("/status")
def status(): return model_status()

@router.post("/predict")
def ml_predict(payload: MLPredictRequest): return predict(payload.model_dump())
