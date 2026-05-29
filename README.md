# Greenhouse AI Monitor

Camera + sensor based monitoring for rooftop / grow-bag vegetable systems.

## MVP scope

Initial target:

- 1 camera
- 2 grow bags
- fixed ROI based image analysis
- soil moisture per bag
- shared temperature / humidity
- shared light sensor
- MQTT output for Home Assistant
- no ML/Hailo dependency in v0

Later phases add Hailo-8 inference, plant segmentation, weed detection, disease/stress classification, and crop-specific intervention logic.

## Architecture

```text
Camera / Frigate snapshot
        ↓
greenhouse-ai-monitor analyzer
        ↓
OpenCV metrics per grow bag
        ↓
Sensor values from MQTT
        ↓
Rules engine
        ↓
MQTT alerts / Home Assistant
```

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

## MQTT topics

```text
grow/bag1/metrics
grow/bag1/alerts
grow/bag2/metrics
grow/bag2/alerts
```

## MVP crop setup

```text
bag1: tomato
bag2: spinach / leafy crop
```

See `docs/ROADMAP.md` and `docs/SENSOR_PLAN.md`.
