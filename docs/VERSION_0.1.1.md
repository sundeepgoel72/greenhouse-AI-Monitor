# Version 0.1.1

Released: 2026-06-03

## Summary

Version `0.1.1` is an operational rebaseline release for the HP400 deployment of Greenhouse AI Monitor. It does not change the deployed architecture, but it captures the current runtime findings, resets the roadmap around verified production behavior, and promotes the daylight-only validity rule for overhead snapshot analysis.

## Rebaseline Findings

- Snapshot collection is active and storing data at roughly 30-minute intervals.
- Daylight overhead frames are usable for ROI-based canopy and soil estimation.
- Overnight `RoofBigPolyhouse` frames switch to monochrome IR and are not valid for the current HSV-based analysis path.
- Operational rule: treat snapshot analysis as valid only from 1 hour after sunrise until 1 hour before sunset.
- The current database review on 2026-06-03 showed 74 snapshots, 296 metrics, 150 sensor readings, and 201 alerts.
- Sensor history contains plausible daytime trends plus obvious startup/source outliers, including `128.4 °C` and `119.4%`.
- Alert noise is currently dominated by repeated canopy-critical entries from overnight IR-driven zero metrics.

## Release Intent

This release rebaselines the repo around the verified operating state before the next code changes:

- daylight-window gating for snapshot analysis
- snapshot alert de-duplication
- sensor validation and timezone-safe timestamps
- daylight ROI review, especially Bed 4
- snapshot path and runtime ownership cleanup

## Version Markers

- Backend app version: `0.1.1`
- Frontend package version: `0.1.1`
- Git tag: `v0.1.1`
