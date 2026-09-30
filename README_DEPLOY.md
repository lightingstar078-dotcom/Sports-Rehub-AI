# Vercel + Render deployment checklist

## Vercel
Create a Vercel project pointing to this repository and set Root Directory to `frontend`.

Build command:
`npm run build`

Output directory:
`dist`

Environment:
`VITE_API_URL=https://YOUR-RENDER-SERVICE.onrender.com`
`VITE_LOCAL_API_URL=http://127.0.0.1:8000`

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

The included `render.yaml` can be used as a Blueprint starting point.

## Video storage
For the deployed service, configure an object storage provider when you want durable cloud video storage. The code intentionally does not claim that local Render filesystem storage is durable cloud storage.
