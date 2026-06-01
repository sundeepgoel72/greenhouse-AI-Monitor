# HP400 Deployment

Native Linux deployment is the primary target for the current MVP.

## Runtime

Backend:

* FastAPI
* SQLite
* Frigate snapshot ingestion
* Home Assistant sensor ingestion
* MQTT publish best-effort

Frontend:

* React/Vite static build served by Vite preview

## Directory

Current HP400 path:

```bash
cd /mnt/ssd/greenhouse-AI-Monitor
```

## Backend Environment

Runtime secrets live in `backend/.env`. This file is intentionally ignored by git.

Minimum local config:

```env
DATABASE_URL=sqlite:///./greenhouse.db
FRIGATE_BASE_URL=http://localhost:5000
FRIGATE_CAMERA=RoofBigPolyhouse

MQTT_HOST=localhost
MQTT_PORT=1883

SNAPSHOT_DIR=./snapshots
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SCHEDULED_INGEST_ENABLED=true
ANALYSIS_INTERVAL_SECONDS=1800

HOME_ASSISTANT_BASE_URL=http://192.168.1.72:8123
HOME_ASSISTANT_TOKEN=<long-lived-token>
HOME_ASSISTANT_SENSORS=[{"entity_id":"sensor.roofbigpolyhouse_bigpolyhouse_temperature","sensor_type":"temperature","unit":"°C"},{"entity_id":"sensor.roofbigpolyhouse_bigpolyhouse_humidity","sensor_type":"humidity","unit":"%"}]
```

## Manual Run

Backend:

```bash
cd /mnt/ssd/greenhouse-AI-Monitor/backend
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8088
```

Frontend:

```bash
cd /mnt/ssd/greenhouse-AI-Monitor/frontend
npm run build
npm run preview -- --host 0.0.0.0 --port 5173
```

## Systemd Install

Install or refresh services:

```bash
cd /mnt/ssd/greenhouse-AI-Monitor
sudo scripts/install_systemd.sh
```

This installs:

* `greenhouse-backend.service`
* `greenhouse-frontend.service`

Service files are stored in:

```text
deploy/systemd/
```

Check status:

```bash
systemctl status greenhouse-backend.service greenhouse-frontend.service
```

View logs:

```bash
journalctl -u greenhouse-backend.service -f
journalctl -u greenhouse-frontend.service -f
```

Restart:

```bash
sudo systemctl restart greenhouse-backend.service greenhouse-frontend.service
```

## Smoke Check

```bash
cd /mnt/ssd/greenhouse-AI-Monitor
scripts/smoke_check.sh
```

The smoke check verifies:

* Backend health
* Beds API
* Latest snapshot API
* Sensor readings API
* Frontend HTTP response

## URLs

Backend:

```text
http://localhost:8088
```

Frontend:

```text
http://localhost:5173
```

Frigate snapshot source:

```text
http://localhost:5000/api/RoofBigPolyhouse/latest.jpg
```

Home Assistant:

```text
http://192.168.1.72:8123
```

## Storage

SQLite:

```text
backend/greenhouse.db
```

Snapshots:

```text
backend/snapshots/
```

Frontend build:

```text
frontend/dist/
```

## Notes

* The scheduler waits one full `ANALYSIS_INTERVAL_SECONDS` interval after backend startup before the first automatic ingestion.
* Manual Frigate ingestion remains available from the dashboard.
* Home Assistant readings are ingested only when `HOME_ASSISTANT_SENSORS` is configured.
* BigPolyHouse temperature/humidity values were fixed on 2026-06-01; latest verified values were 40.1 °C and 41.3%.
