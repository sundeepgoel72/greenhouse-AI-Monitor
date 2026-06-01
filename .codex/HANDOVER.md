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
* Default Frigate camera: `RoofBigPolyhouse`
* OpenCV polygon ROI metrics and ingestion in `backend/services/metrics_engine.py`
* MQTT publisher in `backend/services/mqtt_publisher.py`
* Rule-based alert generation during snapshot ingestion
* Configurable HSV and alert thresholds via `.env`

Frontend:

* React/Vite/TypeScript scaffold in `frontend/`
* Dashboard metric cards
* Snapshot upload
* Frigate ingestion button
* ROI polygon calibration canvas
* ROI point add, undo, clear, drag, and save flows
* Metrics table
* Recent alerts panel
* Selected-bed green/yellow/soil trend sparklines
* Manual observations form/list
* Four-bed seed action
* Recent sensor readings panel
* Sensor-based alerts for high temperature, low/high humidity, and stale sensor data
* Generic external plant/disease identification API endpoint

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

Tune OpenCV and alert thresholds in `.env`:

```text
GREEN_HSV_LOWER=35,35,35
GREEN_HSV_UPPER=90,255,255
YELLOW_HSV_LOWER=22,95,90
YELLOW_HSV_UPPER=34,255,255
SOIL_HSV_LOWER=5,20,20
SOIL_HSV_UPPER=25,210,220

ALERT_GREEN_CRITICAL_BELOW=15
ALERT_GREEN_WARNING_BELOW=30
ALERT_YELLOW_CRITICAL_ABOVE=15
ALERT_YELLOW_WARNING_ABOVE=8
ALERT_SOIL_WARNING_ABOVE=65
ALERT_TEMP_WARNING_ABOVE=38
ALERT_TEMP_CRITICAL_ABOVE=45
ALERT_HUMIDITY_WARNING_BELOW=35
ALERT_HUMIDITY_WARNING_ABOVE=85
ALERT_SENSOR_STALE_MINUTES=60

SCHEDULED_INGEST_ENABLED=true
ANALYSIS_INTERVAL_SECONDS=1800

HOME_ASSISTANT_BASE_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=
HOME_ASSISTANT_SENSORS=[]

PLANT_IDENTIFICATION_API_URL=
PLANT_IDENTIFICATION_API_KEY=
DISEASE_IDENTIFICATION_API_URL=
DISEASE_IDENTIFICATION_API_KEY=
EXTERNAL_DIAGNOSIS_API_KEY_HEADER=Api-Key
EXTERNAL_DIAGNOSIS_IMAGE_FIELD=image
```

## Runtime URLs

Backend:

* `http://localhost:8088`

Frigate camera:

* `RoofBigPolyhouse`

Frontend:

* `http://localhost:5173`

Health check:

* `http://localhost:8088/api/health`

Systemd services:

* `greenhouse-backend.service`
* `greenhouse-frontend.service`

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
* `GET /api/beds/{bed_id}/metrics/history`

Operational data:

* `GET /api/alerts`
* `POST /api/alerts`
* `GET /api/observations`
* `POST /api/observations`
* `GET /api/sensor-readings`
* `POST /api/sensor-readings`
* `POST /api/sensor-readings/home-assistant`
* `POST /api/diagnostics/external`

## Verification Already Done

Successful:

```bash
python3 -m compileall backend
backend/.venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); from app.main import app; print(app.title)"
cd frontend && npm run build
backend/.venv/bin/python -m pytest backend/tests
curl -s http://localhost:8088/api/health
curl -s -I http://localhost:5173/
curl -s -X POST http://localhost:8088/api/ingest/frigate
scripts/smoke_check.sh
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
* `09afee2 feat(p0): add project context handover`
* `6a16e6c feat(p0): generate metric alerts`
* `b170d14 feat(p0): improve roi polygon editing`
* `636e15a feat(p0): update continuation tasklist`
* `21cd2b8 feat(p0): make metric thresholds configurable`
* `1ffd301 feat(p0): add metric history trends`
* `c8d63b8 feat(p0): add backend metrics tests`
* `c51b599 feat(p0): refresh handover after hardening`
* `7aadac0 feat(p0): use polyhouse frigate camera`
* `3c30b0e feat(p0): calibrate polyhouse beds`
* `4365ecf feat(p0): add home assistant sensors`
* `feba640 feat(p0): add hp400 systemd deployment`

## Current Caveats

* No reference polyhouse image was present in `assets/reference`, so calibration uses uploaded/latest snapshots.
* Polygons were recalibrated after the camera angle changed on 2026-06-01.
* ROI calibration supports click-to-add, undo, clear, drag, and save.
* Alert rules are initial configurable threshold rules and need real snapshot tuning.
* Sensor readings storage exists, and Home Assistant ingestion is implemented for mapped numeric entities.
* BigPolyHouse temperature/humidity entities are mapped locally in ignored `backend/.env`.
* BigPolyHouse sensor source is fixed as of 2026-06-01; latest values were 40.1 °C and 41.3%.
* External plant/disease diagnosis is a generic API wrapper and needs provider URLs/API keys before use.
* MQTT publishing is best-effort. If the broker is unavailable, ingestion still persists metrics and alerts.
* Yellow HSV was tightened to avoid classifying dry soil as yellowing on the rooftop camera.

## Latest Calibration Snapshot

Captured through Frigate on 2026-06-01:

* `snapshots/RoofBigPolyhouse/2026-06-01/100729.jpg`
* `snapshots/RoofBigPolyhouse/2026-06-01/115712.jpg` after camera angle change

Saved approximate bed layout:

* Bed 1: top-left bed
* Bed 2: top-right bed
* Bed 3: bottom-left bed
* Bed 4: bottom-right bed

Latest metrics after camera-angle recalibration:

* Bed 1: green 76.29%, yellow 0.02%, soil 2.37%
* Bed 2: green 41.22%, yellow 0.0%, soil 26.35%
* Bed 3: green 49.04%, yellow 1.2%, soil 34.75%
* Bed 4: green 26.69%, yellow 1.05%, soil 56.91%

Current alert:

* Bed 4 warning low canopy.

## Recommended Next Steps

1. Continue HSV and alert threshold tuning in `.env` using more real snapshots across lighting conditions.
2. Add Home Assistant mappings when lux and soil moisture entities become available.
3. Configure external plant/disease provider URLs and API keys when chosen.
4. Add close-up upload workflow in dashboard for disease diagnosis.
5. Install or refresh systemd services with `sudo scripts/install_systemd.sh`.
