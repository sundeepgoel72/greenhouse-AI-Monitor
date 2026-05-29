# ROI Calibration UI

## Purpose

Allow a user to:

1. Load latest Frigate snapshot
2. Draw rectangular grow-bag ROIs
3. Assign crop type
4. Record sowing date
5. Record transplant date (optional)
6. Record expected harvest date (optional)
7. Save configuration

## Bag Fields

- bag_id
- crop
- sowing_date
- transplant_date
- expected_harvest_date
- roi.x
- roi.y
- roi.width
- roi.height

## Future Fields

- variety
- soil type
- irrigation zone
- fertiliser schedule
- notes

## MVP Workflow

Open snapshot
→ Draw ROI
→ Select crop
→ Enter sowing date
→ Save

Output:

bags.yaml
