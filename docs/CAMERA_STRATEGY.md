# Camera Strategy

## MVP Decision

Use the existing Frigate camera for the rooftop growhouse.

Initial monitoring will cover 2 grow bags, with the option to expand to 4 bags if the image quality is sufficient.

## Wide View vs Closeup View

### Wide fixed view

Good for:

- Growth trend
- Green coverage percentage
- Wilting / drooping trend
- Missing growth
- Uneven growth between bags
- Weed-like growth in soil area
- Watering stress when combined with soil moisture
- Light/shade issues when combined with lux readings

Limitations:

- May not show early pest damage
- May not show small disease spots
- May not show leaf texture clearly
- May miss nutrient deficiency until visible at canopy level

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
  - used for growth, coverage, stress trend, alerts

Tier 2: Closeup leaf image
  - manual at first
  - later fixed closeup camera or movable inspection camera
  - used for disease/pest/nutrient analysis
```

## MVP Approach

Do not block MVP on closeup images.

Phase 1 should work with the wide Frigate camera only:

- define ROI for bag1 and bag2
- calculate green coverage
- calculate yellow/brown coverage
- combine with soil moisture
- publish MQTT metrics and alerts

Phase 2 can add closeup capture:

- manual phone photo upload
- second fixed camera
- ESP32-CAM / USB camera
- crop-specific leaf health classifier

## Scale Guidance

For a 50 ft x 20 ft growhouse:

- 1 camera can monitor 2 to 4 bags well
- 1 camera may monitor all 12 bags only at a coarse level
- 3 to 4 cameras is more realistic for reliable 12-bag monitoring
- closeup leaf diagnostics will probably need a separate closeup workflow
