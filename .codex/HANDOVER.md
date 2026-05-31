# Greenhouse AI Monitor Handover

Updated: 2026-05-31

## Current State

P0 MVP backend and frontend scaffold is implemented.

Architecture remains:

Frigate Snapshot
→ Polygon ROI
→ OpenCV Metrics
→ SQLite
→ MQTT
→ Dashboard

## Implemented

Backend:

* FastAPI app in `backend/app/main.py`
* SQLite/SQLAlchemy setup in `backend/app/database.py`
* Models in `backend/app/models.py`
* Schemas in `backend/app/schemas.py`
* CRUD helpers in `backend/app/crud.py`
* Frigate latest snapshot fetcher in `backend/services/frigate_client.py`
* OpenCV polygon ROI metrics and ingestion in `backend/services/metrics_engine.py`
* MQTT publisher in `backend/services/mqtt_publisher.py`

Frontend:

* React/Vite/TypeScript scaffold in `frontend/`
* Dashboard metric cards
* Snapshot upload
* Frigate ingestion button
* ROI polygon calibration canvas
* Metrics table
* Manual observations form/list
* Four-bed seed action

## Important Commands

Install backend dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run backend:

```bash
cd backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8088
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Run frontend:

```bash
cd frontend
npm run dev
```

Build frontend:

```bash
cd frontend
npm run build
```

## Runtime URLs

Backend:

* `http://localhost:8088`

Frontend:

* `http://localhost:5173`

Health check:

* `http://localhost:8088/api/health`

## API Endpoints

Core:

* `GET /api/health`
* `GET /api/beds`
* `POST /api/beds`
* `GET /api/beds/{bed_id}`
* `PUT /api/beds/{bed_id}`

Snapshots and metrics:

* `GET /api/snapshots`
* `GET /api/snapshots/latest`
* `GET /api/snapshots/{snapshot_id}/image`
* `POST /api/ingest/frigate`
* `POST /api/ingest/upload`
* `GET /api/metrics`

Operational data:

* `GET /api/alerts`
* `POST /api/alerts`
* `GET /api/observations`
* `POST /api/observations`
* `POST /api/sensor-readings`

## Verification Already Done

Successful:

```bash
python3 -m compileall backend
backend/.venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); from app.main import app; print(app.title)"
cd frontend && npm run build
curl -s http://localhost:8088/api/health
curl -s -I http://localhost:5173/
```

Backend health returned:

```json
{"status":"ok"}
```

## Commits

Recent P0 commits:

* `e1f7eca feat(p0): add backend api and ingestion pipeline`
* `eff3a68 feat(p0): add greenhouse dashboard scaffold`
* `d2ad75b feat(p0): align frigate fetcher dependencies`
* `a888ffb feat(p0): document local mvp scaffold`

## Current Caveats

* No reference polyhouse image was present in `assets/reference`, so calibration uses uploaded/latest snapshots.
* ROI calibration supports click-to-add, clear, and save. Vertex drag/edit is not implemented.
* Alert storage exists, but rule-based alert generation is not implemented.
* Sensor readings storage exists, but sensor ingestion is not implemented.
* MQTT publishing is best-effort. If the broker is unavailable, ingestion still persists metrics.
* HSV thresholds are initial values and should be tuned with real snapshots.

## Recommended Next Steps

1. Add real rooftop polyhouse snapshot and calibrate four bed polygons.
2. Tune HSV thresholds using actual snapshots.
3. Add rule-based alerts for low green percentage, high yellow percentage, and high soil visibility.
4. Add trend views for each bed.
5. Add sensor ingestion once SHT31/BH1750/soil moisture devices are connected.
