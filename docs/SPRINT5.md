# Sprint 5

## Objectives

- Diagnostic provider abstraction
- OpenAI integration
- Gemini integration
- Diagnosis history
- Observation tracking
- Polygon ROI migration

## New APIs

POST /api/diagnostics/analyze/{photo_id}
GET /api/diagnostics/history/{bed_id}
GET /api/metrics/history/{bed_id}
POST /api/observations

## Context Payload

Crop
Age Days
Temperature
Humidity
Lux
Moisture
Green Coverage
Yellow Coverage

## Output

Diagnosis
Confidence
Recommendations
