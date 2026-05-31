# Greenhouse AI Monitor

MVP implementation for Frigate snapshot based polyhouse monitoring.

## Current scope

- FastAPI backend
- SQLite persistence
- Polygon ROI storage per grow bed
- Frigate latest snapshot ingestion
- OpenCV green/yellow/soil coverage metrics
- MQTT publishing per bed
- React ROI calibration canvas

## Quick start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8088 --reload
```

```bash
cd frontend
npm install
npm run dev
```

## Expected Frigate snapshot URL

```text
http://<frigate-host>:5000/api/<camera_name>/latest.jpg
```
