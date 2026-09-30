# Sports Rehab AI — Offline-First Return-to-Play Monitoring

Created by **Jaisurya ([@Jaisurya2823](https://github.com/Jaisurya2823))**.
Software is licensed under the [MIT License](LICENSE). Third-party datasets
retain their own licenses and attribution; see their dataset documentation.

A hackathon-ready full-stack prototype for **AI-powered Return-to-Play readiness screening and recovery monitoring**.

## Core promise
- Works **offline** for the core assessment pipeline when the local FastAPI service is running.
- Works **online** using the same UI against a deployed Render API.
- No authentication or authorization layer.
- Every assessment video is **compressed with FFmpeg before storage**.
- MediaPipe is used for pose estimation/human validation; the readiness predictor is a separate scikit-learn model.
- No fake ML accuracy is claimed. A real model is produced only after you train it with your research dataset.

> This is a screening/decision-support prototype, not a diagnosis or medical-clearance system. Final return-to-play decisions belong to a qualified healthcare professional.

## Architecture

```text
React + Vite + TypeScript + PWA
              |
      Network / API layer
       /                 \\
      /                   \\
Local FastAPI              Render FastAPI
      |                         |
SQLite + local video       PostgreSQL + object storage*
      |
FFmpeg -> compressed MP4
      |
OpenCV + MediaPipe
      |
Feature extraction
      |
Local Random Forest model
      |
Readiness score + status
      |
Sync queue ---------------> Cloud sync
```

\* Cloud object storage is optional/configurable. The prototype defaults to local storage if cloud storage credentials are not configured.

## Important model requirement
This package now includes a **synthetic development-trained Random Forest** so the end-to-end software pipeline can run immediately. It is explicitly marked `demo=true` and is not clinical evidence. When a real extracted dataset exists, the training script automatically prefers it and writes `demo=false`.

## Local development — Windows PowerShell

### 1. Prerequisites
- Python 3.13 recommended
- Node.js 24+
- FFmpeg on PATH
- MediaPipe Python 1.0.1
- A MediaPipe Pose Landmarker `.task` model file at `backend/models/pose_landmarker_full.task`

Download it with `python scripts\download_pose_model.py`. The backend refuses to pretend pose analysis worked if the model is missing.

### 2. Backend

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

API: `http://127.0.0.1:8000`
Docs: `http://127.0.0.1:8000/docs`

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

### 4. Frontend environment
Copy `.env.example` to `.env` when using a deployed API:

```text
VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com
VITE_LOCAL_API_URL=http://127.0.0.1:8000
```

For a local-only demo leave `VITE_API_URL` empty; the application will use local FastAPI.

## Training the readiness model

### Immediate end-to-end development model
Run:

```powershell
python ml_training\build_development_dataset.py
python ml_training\train_model.py
python ml_training\evaluate_model.py
```

This creates a synthetic development dataset and a trained model marked `demo=true`. Do not use its metrics as clinical or real-world evidence.

### Real athlete-data model

Put controlled videos in:

```text
dataset/raw/squat/
dataset/raw/single_leg_hop/
dataset/raw/single_leg_balance/
```

Create `dataset/labels.csv` with:

```csv
video_id,exercise,pain_score,psychological_readiness,label
squat_001,squat,2,82,GREEN
squat_002,squat,6,55,YELLOW
...
```

Then:

```powershell
python ml_training/extract_dataset.py
python ml_training/train_model.py
python ml_training/evaluate_model.py
```

The resulting model is written to `backend/ml/saved_model/readiness_model.joblib`. When real extracted data is used, the model metadata is marked `demo=false`.

### Dataset note
Treat this as a **prototype research dataset**, not a clinically validated dataset. Do not use evaluation numbers from a demonstration or toy dataset as clinical evidence.

## Test cases
The backend and UI are designed around these gates:

1. Empty room -> NO HUMAN
2. Chair -> NO HUMAN
3. Bag -> NO HUMAN
4. Football -> NO HUMAN
5. Person -> HUMAN DETECTED
6. Partial person -> FULL BODY NOT VISIBLE
7. Person leaves -> assessment pauses / stops

## Deployment

### Vercel frontend
- Root Directory: `frontend`
- Framework preset: Vite
- Build command: `npm run build`
- Output: `dist`

`frontend/vercel.json` contains SPA fallback routing.

### Render backend
- Root Directory: `backend`
- Runtime: Python 3
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

`render.yaml` is included for Blueprint deployment.

Render's current native Python runtime includes FFmpeg, so Docker is intentionally not used by this project.

## API overview

- `GET /api/health`
- `GET /api/system/status`
- `GET /api/athletes`
- `GET /api/athletes/{id}`
- `POST /api/athletes`
- `POST /api/vision/detect-human`
- `POST /api/vision/analyze`
- `POST /api/assessment`
- `GET /api/assessments`
- `GET /api/assessments/{id}`
- `GET /api/recovery/{athlete_id}`
- `POST /api/ml/predict`
- `GET /api/ml/status`
- `POST /api/chat`
- `GET /api/sync/status`
- `POST /api/sync/push`

## Medical wording
Use:
- "Readiness indicator"
- "Further Return-to-Play evaluation"
- "Professional assessment recommended"

Do not use:
- "100% safe"
- "Fully recovered"
- "Safe to play"
- "Guaranteed injury-free"
- "Medically cleared"

## Current build note

The packaged `backend/ml/saved_model/readiness_model.joblib` is a **synthetic development-trained model** and is marked `demo=true`. It exists so the complete application can execute end-to-end without a missing-model error. Replace it by training from controlled athlete data before treating outputs as research findings.

The official MediaPipe `.task` model remains an external binary dependency; run `python scripts\download_pose_model.py` on a machine with internet access and place the result at `backend/models\pose_landmarker_full.task`.
