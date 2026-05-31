Build P0 MVP for Greenhouse AI Monitor.

Architecture:

Frigate Snapshot
→ Polygon ROI
→ OpenCV Metrics
→ SQLite
→ MQTT
→ Dashboard

Implement:

backend/
  FastAPI

frontend/
  React

Features:

1. Bed model
2. ROI polygon storage
3. Snapshot ingestion service
4. Frigate latest.jpg fetcher
5. OpenCV metrics:

   - green_pct
   - yellow_pct
   - soil_pct

6. SQLite persistence

7. MQTT publishing:

   grow/bed1/metrics
   grow/bed2/metrics
   grow/bed3/metrics
   grow/bed4/metrics

8. ROI calibration page

Use uploaded polyhouse image as initial reference.

Do not redesign architecture.

Produce working code.
