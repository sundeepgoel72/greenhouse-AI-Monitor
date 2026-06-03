# Architecture

## Current MVP

```text
Camera
  ↓
Frigate (camera host)
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
Frigate (camera host)
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
