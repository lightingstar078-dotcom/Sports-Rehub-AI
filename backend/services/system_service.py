from pathlib import Path
import os, shutil
from services.video_service import get_ffmpeg_version
from ml.model_service import model_status
from vision.pose_service import pose_status
from services.object_storage import configured as storage_configured
from database import DATABASE_MODE

def system_status():
    return {
        "mode": DATABASE_MODE,
        "local_database": True,
        "ffmpeg": get_ffmpeg_version(),
        "pose_model": pose_status(),
        "local_ml": model_status(),
        "cloud_configured": bool(os.getenv("DATABASE_URL")),
        "object_storage_configured": storage_configured(),
    }
