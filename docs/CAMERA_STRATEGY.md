# Camera Strategy

## MVP Decision

Use the existing Frigate camera for the rooftop polyhouse/growhouse.

The initial monitoring scope is limited to the nearest 4 grow beds only.

Reason:

- The camera has a shallow end-to-end viewing angle.
- Rear beds are visible but have lower effective resolution.
- Growth monitoring for all 12 beds from this one view would be too coarse.
- Reliable leaf or disease inspection is not realistic from this wide view.

## Wide View vs Closeup View

### Wide fixed Frigate view

Good for the nearest 4 beds:

- Growth trend
- Green coverage percentage
- Wilting / drooping trend
- Missing growth
- Uneven growth between beds
- Weed-like growth in soil area
- Watering stress when combined with soil moisture
- Light/shade issues when combined with lux readings

Limitations:

- Rear beds should not be used for MVP analytics from this camera.
- Early pest damage is unlikely to be visible.
- Small leaf disease spots are unlikely to be visible.
- Nutrient deficiency may only be detected once visible at canopy level.

### Closeup leaf view

Needed for:

- Early yellowing
- Leaf spots
- Fungal disease signs
- Pest damage
- Nutrient deficiency patterns
- Leaf curl
- Fine wilting symptoms

## Recommended Operating Model

Use two image tiers:

```text
Tier 1: Wide Frigate snapshot
  - every 30 minutes
  - nearest 4 beds only
  - used for growth, coverage, stress trend, alerts

Tier 2: Closeup leaf image
  - manual at first
  - later fixed closeup camera or movable inspection camera
  - used for disease/pest/nutrient analysis
```

## MVP Approach

Phase 1 should work with the wide Frigate camera only:

- define ROI/polygon for bed1 to bed4
- calculate green coverage
- calculate yellow/brown coverage
- combine with representative soil moisture
- publish MQTT metrics and alerts

Phase 2 can add closeup capture:

- manual phone photo upload
- second fixed closeup camera
- ESP32-CAM / USB camera
- crop-specific leaf health classifier

## Scale Guidance

For a 50 ft x 20 ft growhouse:

- this camera should monitor the nearest 4 beds only
- rear beds need either another camera or a moved/duplicated camera position
- 3 to 4 cameras is more realistic for reliable 12-bed monitoring
- closeup leaf diagnostics will need a separate closeup workflow
