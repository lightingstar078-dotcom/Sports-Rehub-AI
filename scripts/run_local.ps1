$ErrorActionPreference = 'Stop'
Write-Host '=== Sports Rehab AI — Local Offline Runtime ===' -ForegroundColor Cyan
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) { Write-Warning 'FFmpeg is not on PATH. Video compression will fail.' }
if (-not (Test-Path '.\backend\models\pose_landmarker_full.task')) { Write-Warning 'MediaPipe model missing. Run: python scripts\download_pose_model.py' }
Start-Process powershell -ArgumentList '-NoExit','-Command','cd backend; py -3.13 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py'
Start-Process powershell -ArgumentList '-NoExit','-Command','cd frontend; npm install; npm run dev'
