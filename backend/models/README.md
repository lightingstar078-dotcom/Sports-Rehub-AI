# MediaPipe Pose Landmarker model

The backend expects the official MediaPipe Pose Landmarker `.task` asset here:

`backend/models/pose_landmarker_full.task`

The project intentionally does not silently replace the asset with object detection. If the file is absent, pose-dependent analysis fails with `POSE_MODEL_MISSING`.

Download helper:

```powershell
python scripts\download_pose_model.py
```
