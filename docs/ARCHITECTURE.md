# Architecture

## Current MVP

```text
Camera
  ↓
Frigate (HP400)
  ↓
Snapshot Extraction
  ↓
Greenhouse AI Monitor
  ↓
MQTT
  ↓
Home Assistant
```

## Future Architecture

```text
Camera
  ↓
Frigate (HP400)
  ↓
Greenhouse AI Monitor
  ↓
RPi5 + Hailo-8
  ↓
MQTT
  ↓
Home Assistant
```

## Sensors

Shared:
- SHT31
- BH1750

Per Bag:
- Capacitive soil moisture sensor

Controller:
- ESP32
