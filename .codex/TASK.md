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

---

Continuation task list.

Updated: 2026-05-31

P0 MVP baseline has been implemented and committed. Continue from the current repository state.

Next implementation milestones:

1. Configurable thresholds

   - Move OpenCV HSV color thresholds into backend configuration.
   - Move alert thresholds into backend configuration.
   - Keep sensible defaults for green/yellow/soil and alert severities.
   - Do not introduce ML.

2. Trends

   - Add backend API for per-bed metric history.
   - Add compact dashboard trend display for green/yellow/soil over recent snapshots.

3. Tests

   - Add focused backend tests for polygon ROI metric calculation.
   - Add focused backend tests for alert generation thresholds.
   - Add an ingestion persistence test if practical with a generated image fixture.

4. Documentation and handover

   - Keep `.codex/PROJECT_CONTEXT.md` current.
   - Keep `.codex/HANDOVER.md` current.
   - Commit each logical milestone as `feat(p0): ...`.

Current known caveats:

- No real polyhouse reference image is committed.
- HSV and alert thresholds are initial values and need real-snapshot tuning.
- Sensor ingestion is not implemented yet.
- Trend views are not implemented yet.
