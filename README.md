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
- Per-bed metric history and dashboard sparklines
- Generic Home Assistant sensor ingestion for temperature, humidity, lux, soil moisture, or other numeric entities
- Scheduled Frigate snapshot ingestion

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

Backend tests:

```bash
backend/.venv/bin/python -m pytest backend/tests
```

Optional local environment:

```bash
cp .env.example .env
```

The frontend reads `VITE_API_BASE_URL`; by default it uses `http://localhost:8088`.

## Scheduled camera ingestion

The backend can ingest the Frigate snapshot on a fixed interval:

```text
SCHEDULED_INGEST_ENABLED=true
ANALYSIS_INTERVAL_SECONDS=1800
```

The scheduler waits one full interval after backend startup before its first automatic ingestion. Manual ingestion remains available from the dashboard.

## Home Assistant sensors

Create a Home Assistant long-lived access token and map any numeric entities through `.env`:

```text
HOME_ASSISTANT_BASE_URL=http://homeassistant.local:8123
HOME_ASSISTANT_TOKEN=your-long-lived-access-token
HOME_ASSISTANT_SENSORS=[{"entity_id":"sensor.polyhouse_temperature","sensor_type":"temperature","unit":"C"},{"entity_id":"sensor.polyhouse_humidity","sensor_type":"humidity","unit":"%"},{"entity_id":"sensor.bed_1_soil_moisture","sensor_type":"soil_moisture","unit":"%","bed_id":1}]
```

Use any `sensor_type` name for other parameters, such as `lux`, `soil_moisture`, `vpd`, or `co2`. Omit `bed_id` for whole-polyhouse readings.

## Tunable thresholds

OpenCV HSV ranges and alert thresholds can be changed in `.env` without code edits:

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
```

## P0 endpoints

- `GET /api/beds`
- `POST /api/beds`
- `PUT /api/beds/{bed_id}`
- `POST /api/ingest/frigate`
- `POST /api/ingest/upload`
- `GET /api/snapshots/latest`
- `GET /api/metrics`
- `GET /api/beds/{bed_id}/metrics/history`
- `POST /api/observations`
- `POST /api/alerts`
- `GET /api/sensor-readings`
- `POST /api/sensor-readings`
- `POST /api/sensor-readings/home-assistant`

## Expected Frigate snapshot URL

```text
http://<frigate-host>:5000/api/<camera_name>/latest.jpg
```
