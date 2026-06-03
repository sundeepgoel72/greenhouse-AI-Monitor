# Version 0.1.0

Released: 2026-06-01

## Summary

Version `0.1.0` is the first standalone deployment of Greenhouse AI Monitor. It collects Frigate snapshots, applies saved bed ROI polygons, calculates OpenCV canopy metrics, stores results in SQLite, publishes MQTT metrics, ingests Home Assistant environment readings, and serves a React dashboard for monitoring and calibration.

## Implementation

Runtime flow:

```text
Frigate latest.jpg
-> Snapshot ingestion
-> Bed polygon ROI crop/mask
-> OpenCV green/yellow/soil percentage metrics
-> SQLite persistence
-> MQTT publish
-> Dashboard metrics, alerts, trends, and ROI calibration
```

Backend:

- FastAPI service on port `8088`.
- SQLite database at `backend/greenhouse.db`.
- Scheduled ingestion controlled by `SCHEDULED_INGEST_ENABLED` and `ANALYSIS_INTERVAL_SECONDS`.
- Frigate camera key: `main_camera`.
- Generic Home Assistant sensor ingestion through mapped entity IDs.
- Configurable HSV metric thresholds and alert thresholds.
- Generic external plant/disease diagnosis API wrapper for uploaded images.

Frontend:

- React/Vite dashboard on port `5173`.
- Bed cards for latest green/yellow/soil metrics.
- ROI calibration over the latest snapshot.
- All saved bed polygons visible during calibration.
- Sensor freshness badges using `ALERT_SENSOR_STALE_MINUTES`.
- Temperature and humidity trend sparklines.
- Close-up upload panel for external diagnosis providers.

Deployment:

- `greenhouse-backend.service`
- `greenhouse-frontend.service`
- Systemd install script: `scripts/install_systemd.sh`
- Smoke check script: `scripts/smoke_check.sh`
- Regression check script: `scripts/regression_check.sh`

## Usage

Open the dashboard:

```text
http://localhost:5173
```

Backend API:

```text
http://localhost:8088
```

Primary dashboard actions:

- `Refresh`: reload latest data.
- `Frigate`: manually fetch and process the latest Frigate snapshot.
- `Sensors`: manually sync configured Home Assistant sensor readings.
- `Upload`: process an image file as a snapshot.
- `Save` in ROI calibration: save the selected bed polygon.
- `Analyze` in Diagnosis: send a close-up image to the configured plant or disease API.

Runtime configuration is in ignored file `backend/.env`. Required local integrations:

```env
FRIGATE_BASE_URL=http://localhost:5000
FRIGATE_CAMERA=main_camera
HOME_ASSISTANT_BASE_URL=http://<home-assistant-host>:8123
HOME_ASSISTANT_TOKEN=<long-lived-token>
HOME_ASSISTANT_SENSORS=[{"entity_id":"sensor.polyhouse_temperature","sensor_type":"temperature","unit":"°C"},{"entity_id":"sensor.polyhouse_humidity","sensor_type":"humidity","unit":"%"}]
```

Plant/disease providers are optional until accounts and API keys are configured:

```env
PLANT_IDENTIFICATION_API_URL=
PLANT_IDENTIFICATION_API_KEY=
DISEASE_IDENTIFICATION_API_URL=
DISEASE_IDENTIFICATION_API_KEY=
EXTERNAL_DIAGNOSIS_API_KEY_HEADER=Api-Key
EXTERNAL_DIAGNOSIS_IMAGE_FIELD=image
```

## Operations

Restart services:

```bash
sudo systemctl restart greenhouse-backend.service greenhouse-frontend.service
```

Check services:

```bash
systemctl --no-pager --full status greenhouse-backend.service greenhouse-frontend.service
```

Run smoke checks:

```bash
scripts/smoke_check.sh
```

Run regression checks:

```bash
scripts/regression_check.sh
```

The regression script runs backend tests, frontend production build, HTTP smoke checks, config and sensor endpoint checks, and systemd active checks.

## Regression Result

Last verified on the local deployment host:

- Backend tests: `8 passed`.
- Frontend production build: passed.
- HTTP smoke checks: passed.
- `/api/config`: returned `alert_sensor_stale_minutes=60`.
- Recent polyhouse readings were available.
- Backend and frontend systemd services were active.

## Remaining Work

- Tune sensor thresholds after a full day of readings.
- Refine ROI polygons and HSV thresholds from more daylight snapshots.
- Configure concrete external plant and disease identification providers.
- Add lux and soil moisture Home Assistant entities when sensors are available.
