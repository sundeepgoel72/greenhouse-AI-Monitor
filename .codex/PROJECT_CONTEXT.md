# Greenhouse AI Monitor – Codex Project Context

## Objective

Build an AI-assisted monitoring system for a rooftop greenhouse/polyhouse.

Initial deployment:

* 50 ft x 20 ft rooftop polyhouse
* 4 monitored grow beds/grow bags initially
* Expand to 12 beds later

System should identify:

* Growth lagging
* Water stress
* Light issues
* Temperature stress
* Humidity stress
* Nutrient deficiency indicators
* Disease indicators

and generate actionable alerts.

---

## Existing Hardware

### HP400

Primary server.

Runs:

* FastAPI backend
* React frontend
* SQLite
* MQTT
* Frigate

Development target:

* Native Linux first
* Docker later

### Raspberry Pi 5 + Hailo8

Future phase only.

Potential uses:

* Disease inference
* Local vision processing

Not required for MVP.

---

## Existing Software

### Frigate

Already deployed.

Contains rooftop greenhouse camera.

Current deployment:

* One camera
* Four monitored beds

Camera height approximately:

* 6 ft above beds

Snapshots are the primary image source.

---

## Fixed Architecture

Frigate Snapshot
↓
ROI Polygon
↓
OpenCV Analysis
↓
Metrics
↓
SQLite
↓
MQTT
↓
Dashboard

Do not redesign this architecture.

Implement it.

---

## MVP Image Metrics

Per bed:

* green_pct
* yellow_pct
* soil_pct
* snapshot_timestamp

Future:

* flower_count
* fruit_count
* canopy_density

---

## Sensor Metrics

Future sensors:

* Temperature (SHT31)
* Humidity (SHT31)
* Lux (BH1750)
* Soil moisture

Design database to support these now.

---

## ROI Strategy

Use polygons.

Do NOT use rectangles.

Camera has perspective distortion.

Each bed stores:

* crop
* sowing_date
* transplant_date
* polygon coordinates

---

## Current Camera Validation

Camera position has already been reviewed.

Current image quality is sufficient for:

* Green coverage %
* Soil visibility %
* Growth trend

Current image quality is NOT sufficient for:

* Leaf disease diagnosis
* Flower counting
* Fruit counting

These require close-up uploads later.

---

## Database Entities

Required:

### beds

* id
* name
* crop
* sowing_date
* transplant_date
* polygon_json

### snapshots

* id
* timestamp
* image_path

### metrics

* id
* bed_id
* snapshot_id
* green_pct
* yellow_pct
* soil_pct
* created_at

### alerts

* id
* bed_id
* severity
* message
* created_at

### observations

Manual user observations:

* Watered
* Fertilized
* Pruned
* Harvested
* Note

Treat observations as first-class data.

---

## MQTT Topics

Metrics:

* grow/bed1/metrics
* grow/bed2/metrics
* grow/bed3/metrics
* grow/bed4/metrics

Alerts:

* grow/bed1/alerts
* grow/bed2/alerts
* grow/bed3/alerts
* grow/bed4/alerts

Use topic templates, not hardcoded bed numbers.

---

## P0 Implementation Tasks

### Backend

FastAPI

Create:

backend/app/main.py

backend/app/database.py

backend/app/models/

backend/app/services/

backend/app/api/

Implement:

* Bed CRUD
* Snapshot ingestion
* Metrics persistence
* MQTT publishing

---

### Frigate Service

Implement:

services/frigate.py

Functions:

* fetch latest snapshot
* save locally
* return snapshot path

Assume:

http://FRIGATE/api/<camera>/latest.jpg

is configurable.

---

### OpenCV Metrics

Implement:

services/opencv_metrics.py

Input:

* image
* polygon ROI

Output:

{
"green_pct": 32.5,
"yellow_pct": 1.7,
"soil_pct": 65.8
}

Approach:

HSV thresholding initially.

Do not use ML.

---

### MQTT Service

Implement:

services/mqtt.py

Publish:

grow/bedX/metrics

JSON payload.

---

### SQLite

Use SQLAlchemy.

SQLite database:

greenhouse.db

---

## Frontend

React.

Implement:

### ROI Calibration Page

Features:

* Display snapshot
* Draw polygon
* Edit polygon
* Save polygon

### Bed Management Page

Features:

* Create bed
* Edit crop
* Assign polygon

### Dashboard

Show:

* Green %
* Yellow %
* Soil %
* Latest timestamp

No styling work required.

Functionality first.

---

## AI Diagnostics (Future)

Use provider abstraction.

Never hardcode provider.

Planned providers:

* OpenAI
* Gemini
* Plant.id
* Kindwise
* Local models

Not required for MVP.

---

## Mobile Uploads (Future)

Types:

* Leaf
* Fruit
* Flower
* Stem
* Whole plant

Not required for MVP.

---

## Coding Style

Priorities:

1. Working code
2. Simple code
3. Deployable code

Avoid:

* Premature optimization
* Complex abstractions
* Microservices
* Kubernetes
* Docker-first development

Build native Linux implementation first.

---

## Deliverables

Goal is a working vertical slice:

Frigate Snapshot
→ ROI Polygon
→ OpenCV Metrics
→ SQLite
→ MQTT

with actual data flowing end-to-end.

Create logical commits:

feat(p0): database models

feat(p0): frigate snapshot service

feat(p0): roi calibration page

etc.

Continue implementation until blocked.

---

## Current Implementation Status

Updated: 2026-05-31

P0 MVP scaffold is implemented in this repository.

### Backend

Implemented under `backend/`:

* FastAPI app entrypoint: `backend/app/main.py`
* SQLAlchemy setup: `backend/app/database.py`
* SQLite models: `backend/app/models.py`
* Pydantic schemas: `backend/app/schemas.py`
* CRUD helpers: `backend/app/crud.py`
* Frigate latest snapshot fetcher: `backend/services/frigate_client.py`
* OpenCV polygon ROI metrics and snapshot ingestion: `backend/services/metrics_engine.py`
* MQTT publishing helper: `backend/services/mqtt_publisher.py`

Implemented API surface:

* `GET /api/health`
* `GET /api/beds`
* `POST /api/beds`
* `GET /api/beds/{bed_id}`
* `PUT /api/beds/{bed_id}`
* `GET /api/snapshots`
* `GET /api/snapshots/latest`
* `GET /api/snapshots/{snapshot_id}/image`
* `POST /api/ingest/frigate`
* `POST /api/ingest/upload`
* `GET /api/metrics`
* `GET /api/alerts`
* `POST /api/alerts`
* `GET /api/observations`
* `POST /api/observations`
* `POST /api/sensor-readings`

Database tables now cover required P0 entities:

* `beds`
* `snapshots`
* `metrics`
* `alerts`
* `observations`

Future sensor support is represented by:

* `sensor_readings`

OpenCV metrics are HSV-threshold based and return:

* `green_pct`
* `yellow_pct`
* `soil_pct`

MQTT metrics use a topic template:

* `grow/bed{id}/metrics`

MQTT alerts helper exists as:

* `grow/bed{id}/alerts`

Rule-based alert generation now runs during snapshot ingestion for beds with saved polygons:

* very low or low green coverage
* elevated yellowing
* high soil visibility

Generated alerts are persisted and published to:

* `grow/bed{id}/alerts`

MQTT publishing is best-effort. If the broker is unavailable, ingestion still persists snapshots, metrics, and alerts.

### Frontend

Implemented under `frontend/`:

* Vite React TypeScript scaffold
* Dashboard bed metric cards
* Snapshot upload control
* Frigate ingestion button
* ROI calibration canvas using polygons
* ROI point add, undo, clear, drag, and save flows
* ROI save flow via backend `PUT /api/beds/{bed_id}`
* Metrics table
* Recent alerts panel
* Manual observations form and recent observation list
* Seed action to create four initial beds

Frontend default API base:

* `http://localhost:8088`

Override with:

* `VITE_API_BASE_URL`

### Local Run Commands

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8088
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

### Verification Completed

Commands run successfully:

```bash
python3 -m compileall backend
backend/.venv/bin/python -c "import sys; sys.path.insert(0, 'backend'); from app.main import app; print(app.title)"
cd frontend && npm run build
curl -s http://localhost:8088/api/health
curl -s -I http://localhost:5173/
```

Health endpoint returned:

```json
{"status":"ok"}
```

### Commits Created

* `e1f7eca feat(p0): add backend api and ingestion pipeline`
* `eff3a68 feat(p0): add greenhouse dashboard scaffold`
* `d2ad75b feat(p0): align frigate fetcher dependencies`
* `a888ffb feat(p0): document local mvp scaffold`

### Known Caveats

* `.codex/` was initially untracked; it is being added as project context/handover documentation.
* No uploaded polyhouse reference image was present under `assets/reference` during implementation, so the UI supports upload and latest snapshot calibration rather than bundling a reference image.
* ROI point editing is MVP-level but supports click-to-add, undo, clear, drag, and save.
* Alert rules are initial threshold rules only and should be tuned against real greenhouse snapshots.
* Sensor readings API/table exists for future sensors, but no sensor ingestion service is implemented yet.
* OpenCV HSV thresholds are initial values and should be tuned against real greenhouse snapshots.
