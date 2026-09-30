from pathlib import Path
import os

MODEL_PATH = Path(os.getenv("POSE_MODEL_PATH", Path(__file__).resolve().parents[1] / "models" / "pose_landmarker_full.task"))

_image_landmarker = None
_video_landmarker = None

REQUIRED = [0, 11, 12, 23, 24, 25, 26, 27, 28]

def pose_status():
    return {"available": MODEL_PATH.exists(), "path": str(MODEL_PATH)}

def _make(running_mode):
    """Create a landmarker for the matching MediaPipe API/mode."""
    global _image_landmarker, _video_landmarker
    if running_mode == "IMAGE" and _image_landmarker is not None:
        return _image_landmarker
    if running_mode == "VIDEO" and _video_landmarker is not None:
        return _video_landmarker
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Pose model missing: {MODEL_PATH}")
    import mediapipe as mp
    BaseOptions = mp.tasks.BaseOptions
    vision = mp.tasks.vision
    mode = vision.RunningMode.IMAGE if running_mode == "IMAGE" else vision.RunningMode.VIDEO
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=mode,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )
    landmarker = vision.PoseLandmarker.create_from_options(options)
    if running_mode == "IMAGE":
        _image_landmarker = landmarker
    else:
        _video_landmarker = landmarker
    return landmarker

def detect_image_rgb(frame_rgb):
    import mediapipe as mp
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Pose model missing: {MODEL_PATH}")
    import numpy as np
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(frame_rgb))
    landmarker = _make("IMAGE")
    result = landmarker.detect(image)
    return result

def detect_video_frame(frame_bgr, timestamp_ms: int):
    import mediapipe as mp
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_bgr[:, :, ::-1].copy())
    return _make("VIDEO").detect_for_video(image, timestamp_ms)
