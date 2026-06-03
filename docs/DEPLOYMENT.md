# Deployment

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

Use the local checkout path on your deployment host:

```bash
cd <repo-dir>
```

## Backend Environment

Runtime secrets live in `backend/.env`. This file is intentionally ignored by git.

Minimum local config:

```env
DATABASE_URL=sqlite:///./greenhouse.db
FRIGATE_BASE_URL=http://localhost:5000
FRIGATE_CAMERA=main_camera

MQTT_HOST=localhost
MQTT_PORT=1883

SNAPSHOT_DIR=./snapshots
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
SCHEDULED_INGEST_ENABLED=true
ANALYSIS_INTERVAL_SECONDS=1800

HOME_ASSISTANT_BASE_URL=http://<home-assistant-host>:8123
HOME_ASSISTANT_TOKEN=<long-lived-token>
HOME_ASSISTANT_SENSORS=[{"entity_id":"sensor.polyhouse_temperature","sensor_type":"temperature","unit":"°C"},{"entity_id":"sensor.polyhouse_humidity","sensor_type":"humidity","unit":"%"}]

ALERT_TEMP_WARNING_ABOVE=38
ALERT_TEMP_CRITICAL_ABOVE=45
ALERT_HUMIDITY_WARNING_BELOW=35
ALERT_HUMIDITY_WARNING_ABOVE=85
ALERT_SENSOR_STALE_MINUTES=60
ALERT_DEDUPE_MINUTES=60

PLANT_IDENTIFICATION_API_URL=
PLANT_IDENTIFICATION_API_KEY=
DISEASE_IDENTIFICATION_API_URL=
DISEASE_IDENTIFICATION_API_KEY=
EXTERNAL_DIAGNOSIS_API_KEY_HEADER=Api-Key
EXTERNAL_DIAGNOSIS_IMAGE_FIELD=image
```

## Manual Run

Backend:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8088
```

Frontend:

```bash
cd frontend
npm run build
npm run preview -- --host 0.0.0.0 --port 5173
```

## Systemd Install

Install or refresh services:

```bash
sudo scripts/install_systemd.sh
```

This installs:

* `greenhouse-backend.service`
* `greenhouse-frontend.service`

Service files are stored in:

```text
deploy/systemd/
```

## Smoke Check

```bash
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
http://localhost:5000/api/<camera-name>/latest.jpg
```

Home Assistant:

```text
http://<home-assistant-host>:8123
```

## Notes

* The scheduler waits one full `ANALYSIS_INTERVAL_SECONDS` interval after backend startup before the first automatic ingestion.
* Manual Frigate ingestion remains available from the dashboard.
* Home Assistant readings are ingested only when `HOME_ASSISTANT_SENSORS` is configured.
* External plant/disease diagnosis requires provider URLs and API keys. Prefer close-up uploads for disease diagnosis; wide Frigate snapshots are best for growth/coverage trends.
* Repeated alerts are suppressed within `ALERT_DEDUPE_MINUTES`.
* If Home Assistant sensor timestamps repeat while backend readings continue to insert, inspect the sensor update path.
* Repo-local helper scripts should derive the checkout root dynamically; deployed systemd units should keep explicit absolute paths that are injected at install time.
