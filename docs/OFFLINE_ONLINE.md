# Offline vs Online operation

## Offline
Run the local FastAPI + React PWA on the same machine. Core processing is local:

Camera/video → FFmpeg → OpenCV/MediaPipe → features → local Random Forest → SQLite.

Internet is not required after dependencies and the MediaPipe model are installed locally.

## Online
Vercel hosts the React frontend. Render hosts FastAPI. Set `VITE_API_URL` on Vercel and `DATABASE_URL` on Render for PostgreSQL. Optional S3-compatible object storage is used for durable compressed videos.

## Sync
Set `CLOUD_API_URL=https://YOUR-RENDER-SERVICE.onrender.com` in the local backend. `POST /api/sync/push` sends pending athlete/assessment records to the Render `POST /api/sync/receive` endpoint.

For a production system, add authentication/authorization before exposing a writeable sync receiver. This hackathon prototype intentionally has no authentication/authorization because that was a locked product constraint.
