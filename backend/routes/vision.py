from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import os
from services.video_service import save_and_compress, video_metadata
from vision.pose_service import detect_image_rgb, pose_status
from vision.human_detector import validate_result, validate_video
from vision.feature_extractor import extract_features

router = APIRouter()

@router.post("/detect-human")
async def detect_human(file: UploadFile = File(...)):
    # Keep OpenCV optional at import time so health/status checks remain useful
    # when a vision dependency has not yet been installed.
    import cv2
    import numpy as np
    raw = await file.read()
    arr = np.frombuffer(raw, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None: raise HTTPException(400, "Invalid image")
    try:
        result = detect_image_rgb(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        return validate_result(result)
    except FileNotFoundError as exc:
        raise HTTPException(503, str(exc))

@router.post("/analyze")
async def analyze_video(file: UploadFile = File(...), exercise: str = Form(...)):
    if exercise not in {"squat","single_leg_hop","single_leg_balance"}:
        raise HTTPException(400, "Unsupported exercise")
    saved = save_and_compress(file)
    try:
        validation = validate_video(saved["path"])
        if not validation["valid"]:
            os.remove(saved["path"])
            raise HTTPException(422, validation.get("message") or "Human validation failed")
        features = extract_features(saved["path"], exercise)
        return {**saved, "metadata": video_metadata(saved["path"]), "human_validation": validation, "features": features}
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        os.remove(saved["path"])
        raise HTTPException(503, str(exc))
    except Exception as exc:
        os.remove(saved["path"])
        raise HTTPException(500, f"Video analysis failed: {exc}")
