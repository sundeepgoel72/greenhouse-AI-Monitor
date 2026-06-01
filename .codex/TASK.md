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

Use the real Frigate polyhouse camera key:

- `RoofBigPolyhouse`

Next implementation milestones:

1. Configurable thresholds

   - Done: Move OpenCV HSV color thresholds into backend configuration.
   - Done: Move alert thresholds into backend configuration.
   - Keep sensible defaults for green/yellow/soil and alert severities.
   - Do not introduce ML.

2. Trends

   - Done: Add backend API for per-bed metric history.
   - Done: Add compact dashboard trend display for green/yellow/soil over recent snapshots.

3. Tests

   - Done: Add focused backend tests for polygon ROI metric calculation.
   - Done: Add focused backend tests for alert generation thresholds.
   - Done: Add an ingestion persistence test with a generated image fixture.

4. Documentation and handover

   - Keep `.codex/PROJECT_CONTEXT.md` current.
   - Keep `.codex/HANDOVER.md` current.
   - Commit each logical milestone as `feat(p0): ...`.
   - Done: Run frontend build checks after dashboard additions.
   - Done: Update default Frigate camera to `RoofBigPolyhouse`.

5. Calibration

   - Done: Ingest a current `RoofBigPolyhouse` snapshot.
   - Done: Create four bed records.
   - Done: Save approximate four-bed polygons from the live camera view.
   - Done: Run ingestion again after polygon calibration.
   - Done: Tighten yellow HSV defaults to reduce dry-soil false positives.
   - Next: Refine polygons in the dashboard against the live image.
   - Next: Continue HSV and alert threshold tuning from more real metrics.

6. Sensor ingestion

   - Done: Add generic Home Assistant sensor ingestion by mapped entity ID.
   - Done: Add recent sensor readings API and dashboard panel.
   - Done: Support whole-polyhouse and per-bed readings through optional `bed_id`.
   - Done: Add configurable high-temperature, humidity, and stale-sensor alert rules.
   - Done: Add real Home Assistant URL/token/entity mappings in ignored `backend/.env`.
   - Next: Tune sensor thresholds after one full day of readings.

7. External diagnosis

   - Done: Add generic external plant/disease identification API wrapper.
   - Done: Add endpoint for uploaded images or latest/specific snapshots.
   - Done: Add dashboard close-up image upload panel for plant/disease diagnosis.
   - Next: Configure concrete provider URL/API keys.

8. Deployment

   - Done: Add native systemd service templates for backend and frontend.
   - Done: Add install script for HP400 systemd deployment.
   - Done: Add smoke check script.
   - Done: Install and enable `greenhouse-backend.service` and `greenhouse-frontend.service`.
   - Done: Verify standalone collection after 30+ minutes with scheduled metric and sensor batches.
   - Next: Monitor Home Assistant timestamp freshness.

Current known caveats:

- Frigate camera default is `RoofBigPolyhouse`.
- Frigate latest snapshot endpoint for `RoofBigPolyhouse` returned `200 image/jpeg` on HP400.
- Bed polygons were recalibrated after the camera angle changed on 2026-06-01.
- HSV and alert thresholds are configurable and need real-snapshot tuning.
- Home Assistant sensor ingestion is implemented, and BigPolyHouse temperature/humidity are configured locally in ignored `backend/.env`.
- BigPolyHouse sensor values are realistic as of 2026-06-01; latest sync returned 40.1 °C and 41.3%.
- HP400 systemd deployment is installed and services are active.
- Home Assistant sensor timestamps repeated during the standalone check; monitor and inspect the HA/ESP update path if it persists.
- Trend views are implemented as selected-bed dashboard sparklines.

---

Add-on task list.

Updated: 2026-06-01

In progress: Sensor freshness, environment trends, ROI refinement.

1. Home Assistant timestamp freshness

   - Add dashboard freshness status for current temperature/humidity readings.
   - Use `ALERT_SENSOR_STALE_MINUTES` / `alert_sensor_stale_minutes` as the shared stale threshold.
   - Keep monitoring BigPolyHouse timestamp freshness; latest readings were updating normally again on 2026-06-01.

2. Temperature and humidity trends

   - Add dashboard sparklines for whole-polyhouse temperature and humidity.
   - Reuse existing `GET /api/sensor-readings?limit=N`.
   - Treat current BigPolyHouse sensors as whole-polyhouse readings because `bed_id` is null.

3. ROI refinement

   - Show all saved bed polygons on the calibration image.
   - Keep the selected bed polygon editable.
   - Add per-bed calibration status so empty or incomplete ROI polygons are visible.

---

TODO list.

Updated: 2026-06-01

1. Regression test suite

   - Create a repeatable regression test suite covering backend APIs, ingestion, sensor freshness, ROI persistence, and dashboard build.
   - Include smoke-level checks for the HP400 systemd deployment.
   - Document the command sequence in project handover notes.

2. Sensor threshold tuning

   - Review one full day of BigPolyHouse temperature and humidity readings.
   - Tune high-temperature, humidity, and stale-sensor thresholds from real data.

3. ROI and HSV tuning

   - Recheck all bed polygons against the changed camera angle after more daylight snapshots.
   - Tune HSV thresholds using real green/yellow/soil metrics from current camera coverage.

4. External diagnosis provider setup

   - Configure concrete plant identification and disease identification provider URLs/API keys.
   - Run one upload test through the dashboard diagnosis panel.

5. Additional sensors

   - Add mapped Home Assistant entities for lux and soil moisture when sensors are available.
   - Confirm whole-polyhouse versus per-bed `bed_id` mapping before enabling alerts.
