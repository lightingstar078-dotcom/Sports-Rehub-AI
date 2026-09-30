# API documentation

## Health / status
`GET /api/health`
`GET /api/system/status`
`GET /api/ml/status`
`GET /api/sync/status`

## Athletes
`GET /api/athletes`
`GET /api/athletes/{id}`
`POST /api/athletes`

## Vision
`POST /api/vision/detect-human` — multipart `file`
`POST /api/vision/analyze` — multipart `file`, `exercise`

## Assessment
`POST /api/assessment` — multipart:
- athlete_id
- exercise
- pain
- psychological_readiness
- psychology_json
- recovery_trend
- file

`GET /api/assessment?athlete_id={id}`
`GET /api/assessment/{id}`

## ML
`POST /api/ml/predict`

## Chat
`POST /api/chat`

## Sync
`POST /api/sync/push`
