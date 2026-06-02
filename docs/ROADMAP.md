# Roadmap

Updated: 2026-06-03

## Current Baseline

- P0 MVP is deployed and storing snapshots, metrics, alerts, and Home Assistant sensor readings.
- Current vision pipeline is useful only during daylight.
- Operational rule: snapshot analysis is valid only from 1 hour after sunrise until 1 hour before sunset.

## Phase 1 — Operational Hardening

- Gate snapshot analysis to the daylight-valid window.
- Skip or explicitly mark overnight IR snapshots as non-analytic.
- Route snapshot alerts through CRUD de-duplication.
- Normalize timestamps so backend and frontend freshness logic agree.
- Make snapshot file resolution independent of backend working directory.
- Fix runtime artifact ownership issues that block local verification and frontend builds.

## Phase 2 — Sensor Quality

- Reject or quarantine impossible sensor values.
- Recompute threshold tuning from cleaned temperature and humidity history.
- Monitor freshness against a timezone-safe timestamp path.
- Add sensor-level diagnostics that distinguish missing data, stale data, and invalid data.

## Phase 3 — Vision Quality

- Recheck all four ROI polygons on current daylight frames.
- Review Bed 4 first because its recent daylight green coverage trails the other beds.
- Continue HSV threshold tuning using only valid daylight imagery.
- Add visibility or scene-quality checks before trusting image metrics.

## Phase 4 — Diagnosis Integration

- Configure concrete plant identification and disease provider credentials.
- Verify one end-to-end upload from the dashboard.
- Preserve close-up uploads as the path for disease assessment rather than overhead snapshots.
- Keep iterating on the mobile-first browser capture flow for per-bed close-up images before considering any native app.

## Phase 5 — Expanded Sensing

- Add lux and soil-moisture entities from Home Assistant when available.
- Confirm whole-polyhouse versus per-bed `bed_id` mapping before enabling new alerts.
- Add crop-specific thresholds once the sensor set is stable.

## Phase 6 — Historical Analytics

- Daily and weekly greenhouse summaries.
- Better trend review for per-bed growth and whole-polyhouse environment.
- Alert quality review based on real operator feedback.

## Phase 7 — Scale and ML

- Multi-camera support if the grow area expands.
- Crop-specific profiles.
- Hailo-8 or external inference only after the daylight and sensor pipeline is stable.
