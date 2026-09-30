# Vercel + Render deployment checklist

## Local `.env` setup (PowerShell)

Run these from the repository root. They create local files only if they do not
already exist, so an existing `.env` (and its secrets) is not overwritten:

```powershell
if (-not (Test-Path backend/.env)) { Copy-Item backend/.env.example backend/.env }
if (-not (Test-Path frontend/.env)) { Copy-Item frontend/.env.example frontend/.env }
```

For local testing, `backend/.env` can use the defaults in its example:

```dotenv
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MAX_UPLOAD_MB=120
SQLITE_PATH=./storage/sports_ai.db
POSE_MODEL_PATH=./models/pose_landmarker_full.task
ML_MODEL_PATH=./ml/saved_model/readiness_model.joblib
DATABASE_URL=
S3_ENDPOINT=
S3_BUCKET=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_REGION=auto
```

Empty `DATABASE_URL` and S3 fields intentionally mean local SQLite/local video
storage; no cloud database or object store is needed to demo locally. Keep real
cloud credentials only in the hosting provider's secret environment settings,
never in Vite variables or Git. The `.env` files are ignored by Git.

For local Vite development, keep both frontend values blank. Vite's `/api`
proxy forwards to `127.0.0.1:8000`:

```dotenv
VITE_API_URL=
VITE_LOCAL_API_URL=
```

Start the backend and frontend in two PowerShell windows from the repository
root (after installing requirements and downloading the pose task model):

```powershell
py -3.13 -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open the localhost URL printed by Vite. Verify the API with
`Invoke-RestMethod http://127.0.0.1:8000/api/health`. Camera access requires
`localhost`/HTTPS and browser permission. Offline mode means the UI uses this
local backend; it does not mean Vercel can run Python while the computer is
offline.

## Vercel
Create a Vercel project pointing to this repository and set Root Directory to `frontend`.

Build command:
`npm run build`

Output directory:
`dist`

Environment:
`VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com`

Set `VITE_API_URL` to the actual HTTPS URL shown by Render, then redeploy the
Vercel project (Vite variables are embedded at build time). The Settings page
can also save/verify an API URL in that browser. Do not enter the Vercel URL as
the API URL. `VITE_LOCAL_API_URL` is optional and should normally be left blank;
local Vite development uses its `/api` proxy, and installed production clients
use `http://127.0.0.1:8000` for local mode by default. It can be set to a
different local FastAPI origin if needed (service root, without `/api`).

The online API needs to be a running Render FastAPI service. Set Render's
`CORS_ORIGINS` to the exact deployed Vercel origin (for example
`https://your-project.vercel.app`), or keep `*` for a temporary test deployment.
The deploy build downloads the MediaPipe pose model; in local development run
`py -3.13 scripts\download_pose_model.py` before starting the backend.

Offline use still requires the local FastAPI runtime, pose model, FFmpeg, and
readiness model on the computer running the browser. The Vercel PWA caches its
frontend shell, not Python/MediaPipe processing. Select **Use Local Offline
Mode** in Settings and keep the local backend running.

## Render
Create a Web Service with Root Directory `backend`.

Runtime: Python 3

Build:
`pip install -r requirements.txt`

Start:
`uvicorn main:app --host 0.0.0.0 --port $PORT`

Environment:
`PYTHON_VERSION=3.13.9`
`CORS_ORIGINS=https://YOUR-VERCEL-DOMAIN.vercel.app`

Only fill `DATABASE_URL` when you have provisioned a compatible PostgreSQL
database, and only fill the `S3_*` settings when you have a compatible bucket.
These are optional integrations, not values that can be guessed or fabricated.

The included `render.yaml` can be used as a Blueprint starting point.

## Video storage
For the deployed service, configure an object storage provider when you want durable cloud video storage. The code intentionally does not claim that local Render filesystem storage is durable cloud storage.
