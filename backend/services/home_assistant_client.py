import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

from app.config import settings
from app.schemas import SensorReadingCreate


@dataclass(frozen=True)
class HomeAssistantSensor:
    entity_id: str
    sensor_type: str
    unit: str | None = None
    bed_id: int | None = None


def configured_sensors(raw: str | None = None) -> list[HomeAssistantSensor]:
    value = settings.home_assistant_sensors if raw is None else raw
    if not value.strip():
        return []
    data = json.loads(value)
    if not isinstance(data, list):
        raise ValueError("HOME_ASSISTANT_SENSORS must be a JSON list")

    sensors: list[HomeAssistantSensor] = []
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("HOME_ASSISTANT_SENSORS entries must be objects")
        entity_id = str(item.get("entity_id") or "").strip()
        sensor_type = str(item.get("sensor_type") or "").strip()
        if not entity_id or not sensor_type:
            raise ValueError("Each Home Assistant sensor needs entity_id and sensor_type")
        unit = item.get("unit")
        bed_id = item.get("bed_id")
        sensors.append(
            HomeAssistantSensor(
                entity_id=entity_id,
                sensor_type=sensor_type,
                unit=str(unit) if unit is not None else None,
                bed_id=int(bed_id) if bed_id is not None else None,
            )
        )
    return sensors


class HomeAssistantClient:
    def __init__(self, base_url: str | None = None, token: str | None = None):
        self.base_url = (base_url or settings.home_assistant_base_url or "").rstrip("/")
        self.token = token or settings.home_assistant_token
        if not self.base_url:
            raise ValueError("HOME_ASSISTANT_BASE_URL is required")
        if not self.token:
            raise ValueError("HOME_ASSISTANT_TOKEN is required")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_state(self, entity_id: str) -> dict[str, Any]:
        response = httpx.get(
            f"{self.base_url}/api/states/{entity_id}",
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def read_sensor(self, sensor: HomeAssistantSensor) -> SensorReadingCreate | None:
        state = self.get_state(sensor.entity_id)
        raw_value = state.get("state")
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None

        attributes = state.get("attributes") or {}
        unit = sensor.unit or attributes.get("unit_of_measurement")
        timestamp = _parse_ha_datetime(state.get("last_updated") or state.get("last_changed"))
        return SensorReadingCreate(
            bed_id=sensor.bed_id,
            sensor_type=sensor.sensor_type,
            value=value,
            unit=unit,
            timestamp=timestamp,
        )

    def read_configured_sensors(self) -> list[SensorReadingCreate]:
        readings: list[SensorReadingCreate] = []
        for sensor in configured_sensors():
            reading = self.read_sensor(sensor)
            if reading is not None:
                readings.append(reading)
        return readings


def _parse_ha_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
