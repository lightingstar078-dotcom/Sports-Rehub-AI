from .pose_service import REQUIRED, detect_video_frame

def _visible(lm):
    vis = getattr(lm, "visibility", None)
    pres = getattr(lm, "presence", None)
    return (vis is None or vis >= 0.55) and (pres is None or pres >= 0.55)

def validate_result(result):
    if not result.pose_landmarks:
        return {"human_detected": False, "full_body_visible": False, "confidence": 0.0, "status": "NO_HUMAN_DETECTED", "message": "No human detected. Please position yourself in front of the camera."}
    lms = result.pose_landmarks[0]
    available = sum(1 for i in REQUIRED if i < len(lms) and _visible(lms[i]))
    confidence = available / len(REQUIRED)
    full = confidence >= 0.78
    return {
        "human_detected": confidence >= 0.45,
        "full_body_visible": full,
        "confidence": round(confidence, 2),
        "status": "READY" if full else ("FULL_BODY_NOT_VISIBLE" if confidence >= 0.45 else "NO_HUMAN_DETECTED"),
        "message": None if full else ("Full body is not visible. Please move back so your full body is inside the camera frame." if confidence >= 0.45 else "No human detected. Please position yourself in front of the camera."),
    }

def validate_video(path: str, sample_limit: int = 60):
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return {"valid": False, "message": "Could not open the video.", "frames_checked": 0, "valid_frames": 0}
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    step = max(1, frames // sample_limit) if frames else 1
    valid_streak = 0
    best = {"confidence": 0, "full_body_visible": False}
    checked = valid_count = 0
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % step != 0:
            idx += 1
            continue
        ts = int((idx / fps) * 1000)
        try:
            state = validate_result(detect_video_frame(frame, ts))
        except FileNotFoundError:
            cap.release()
            return {"valid": False, "error_code": "POSE_MODEL_MISSING", "message": "MediaPipe Pose model is missing. Add backend/models/pose_landmarker_full.task.", "frames_checked": checked, "valid_frames": valid_count}
        checked += 1
        if state["full_body_visible"]:
            valid_count += 1
            valid_streak += 1
        else:
            valid_streak = 0
        if state["confidence"] > best["confidence"]:
            best = state
        if valid_streak >= 5:
            break
        idx += 1
    cap.release()
    ok = checked > 0 and valid_count / checked >= 0.45 and valid_streak >= 5
    return {"valid": ok, "frames_checked": checked, "valid_frames": valid_count, "best": best, "message": None if ok else "Full-body validation did not pass across consecutive frames."}
