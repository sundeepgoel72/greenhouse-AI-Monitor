# Greenhouse AI Monitor

MVP implementation for Frigate snapshot based polyhouse monitoring.

## Current scope

- FastAPI backend
- SQLite persistence
- Polygon ROI storage per grow bed
- Frigate latest snapshot ingestion
- OpenCV green/yellow/soil coverage metrics
- MQTT publishing per bed
- Rule-based metric alerts per bed
- React ROI calibration canvas

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

```bash
cd frontend
npm install
npm run dev
```

Optional local environment:

```bash
cp .env.example .env
```

The frontend reads `VITE_API_BASE_URL`; by default it uses `http://localhost:8088`.

## P0 endpoints

- `GET /api/beds`
- `POST /api/beds`
- `PUT /api/beds/{bed_id}`
- `POST /api/ingest/frigate`
- `POST /api/ingest/upload`
- `GET /api/snapshots/latest`
- `GET /api/metrics`
- `POST /api/observations`
- `POST /api/alerts`

## Expected Frigate snapshot URL

```text
http://<frigate-host>:5000/api/<camera_name>/latest.jpg
```
