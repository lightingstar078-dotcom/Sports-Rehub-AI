from pathlib import Path
import os, subprocess, json, uuid
from fastapi import UploadFile, HTTPException

BASE = Path(__file__).resolve().parent.parent
STORAGE = Path(os.getenv("STORAGE_DIR", BASE / "storage"))
VIDEO_DIR = STORAGE / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)
MAX_MB = int(os.getenv("MAX_UPLOAD_MB", "120"))
ALLOWED = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}

def get_ffmpeg_version():
    try:
        p = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        return p.stdout.splitlines()[0] if p.returncode == 0 and p.stdout else "available"
    except Exception:
        return None

def _safe_ext(name: str | None) -> str:
    ext = Path(name or "").suffix.lower()
    if ext not in ALLOWED:
        raise HTTPException(400, "Unsupported video format. Use MP4, MOV, M4V, WEBM, AVI or MKV.")
    return ext

def save_and_compress(upload: UploadFile) -> dict:
    ext = _safe_ext(upload.filename)
    temp = VIDEO_DIR / f"temp_{uuid.uuid4().hex}{ext}"
    out = VIDEO_DIR / f"assessment_{uuid.uuid4().hex}.mp4"
    size = 0
    with temp.open("wb") as f:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_MB * 1024 * 1024:
                temp.unlink(missing_ok=True)
                raise HTTPException(413, f"Video exceeds {MAX_MB} MB limit.")
            f.write(chunk)
    try:
        cmd = ["ffmpeg", "-y", "-i", str(temp), "-vf", "scale='min(1280,iw)':-2", "-r", "30", "-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-movflags", "+faststart", "-an", str(out)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if p.returncode != 0 or not out.exists():
            raise HTTPException(500, "FFmpeg compression failed. Verify FFmpeg is installed and the video is valid.")
        return {"path": str(out), "original_size": size, "compressed_size": out.stat().st_size}
    finally:
        temp.unlink(missing_ok=True)

def video_metadata(path: str) -> dict:
    import cv2
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return {"duration": 0, "resolution": "unknown", "fps": 0, "frames": 0}
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    return {"duration": round(frames / fps, 2) if fps else 0, "resolution": f"{width}x{height}", "fps": round(fps, 2), "frames": frames}
