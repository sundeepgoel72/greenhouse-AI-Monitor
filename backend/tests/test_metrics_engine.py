import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import cv2
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from services.metrics_engine import MetricsEngine, SnapshotIngestionService
from services.home_assistant_client import (
    HomeAssistantClient,
    HomeAssistantSensor,
    configured_sensors,
)
from services.external_diagnosis_client import ExternalDiagnosisClient
from services.sensor_alerts import sensor_alert_messages


class DummyPublisher:
    def __init__(self):
        self.metrics = []
        self.alerts = []

    def publish_bed_metrics(self, bed_id, metrics):
        self.metrics.append((bed_id, metrics))

    def publish_bed_alert(self, bed_id, alert):
        self.alerts.append((bed_id, alert))


def test_analyze_bed_reports_configured_color_percentages():
    hsv = np.zeros((10, 10, 3), dtype=np.uint8)
    hsv[:4, :] = [45, 180, 180]
    hsv[4:6, :] = [30, 180, 180]
    hsv[6:, :] = [12, 80, 120]
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    polygon = [{"x": 0, "y": 0}, {"x": 9, "y": 0}, {"x": 9, "y": 9}, {"x": 0, "y": 9}]

    metrics = MetricsEngine(publisher=DummyPublisher()).analyze_bed(image, polygon)

    assert metrics["green_pct"] == 40.0
    assert metrics["yellow_pct"] == 20.0
    assert metrics["soil_pct"] == 40.0


def test_generate_alerts_uses_thresholds():
    engine = MetricsEngine(publisher=DummyPublisher())
    metric = SimpleNamespace(green_pct=10, yellow_pct=16, soil_pct=70)

    alerts = engine.generate_alerts(metric)

    assert ("critical", "Canopy coverage is very low. Inspect irrigation, light exposure, and plant establishment.") in alerts
    assert ("critical", "Yellowing is elevated. Inspect for nutrient deficiency, water stress, or disease symptoms.") in alerts
    assert ("warning", "Soil visibility is high. Check canopy development and moisture conditions.") in alerts


def test_ingestion_persists_snapshot_metrics_alerts_and_publishes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'greenhouse.db'}", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()
    publisher = DummyPublisher()

    try:
        bed = models.Bed(
            name="Bed 1",
            crop="Tomato",
            polygon_json=json.dumps(
                [{"x": 0, "y": 0}, {"x": 9, "y": 0}, {"x": 9, "y": 9}, {"x": 0, "y": 9}]
            ),
        )
        db.add(bed)
        db.commit()

        hsv = np.zeros((10, 10, 3), dtype=np.uint8)
        hsv[:, :] = [45, 180, 180]
        image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        image_path = tmp_path / "snapshot.jpg"
        cv2.imwrite(str(image_path), image)

        service = SnapshotIngestionService(db, engine=MetricsEngine(publisher=publisher))
        snapshot, metrics, alerts = service._ingest_path(image_path, datetime(2026, 5, 31))

        assert snapshot.id is not None
        assert len(metrics) == 1
        assert metrics[0].green_pct == 100.0
        assert alerts == []
        assert db.query(models.Snapshot).count() == 1
        assert db.query(models.Metric).count() == 1
        assert publisher.metrics[0][0] == bed.id
    finally:
        db.close()


def test_configured_home_assistant_sensors_are_generic():
    sensors = configured_sensors(
        '[{"entity_id":"sensor.polyhouse_temp","sensor_type":"temperature","unit":"C"},'
        '{"entity_id":"sensor.bed_1_soil","sensor_type":"soil_moisture","unit":"%","bed_id":1}]'
    )

    assert sensors == [
        HomeAssistantSensor(
            entity_id="sensor.polyhouse_temp",
            sensor_type="temperature",
            unit="C",
            bed_id=None,
        ),
        HomeAssistantSensor(
            entity_id="sensor.bed_1_soil",
            sensor_type="soil_moisture",
            unit="%",
            bed_id=1,
        ),
    ]


def test_home_assistant_client_converts_numeric_state(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "state": "27.4",
                "last_updated": "2026-06-01T04:40:00+00:00",
                "attributes": {"unit_of_measurement": "C"},
            }

    def fake_get(url, headers, timeout):
        assert url == "http://ha.local/api/states/sensor.temp"
        assert headers["Authorization"] == "Bearer token"
        assert timeout == 15
        return Response()

    monkeypatch.setattr("services.home_assistant_client.httpx.get", fake_get)
    client = HomeAssistantClient(base_url="http://ha.local", token="token")

    reading = client.read_sensor(
        HomeAssistantSensor(entity_id="sensor.temp", sensor_type="temperature")
    )

    assert reading is not None
    assert reading.sensor_type == "temperature"
    assert reading.value == 27.4
    assert reading.unit == "C"


def test_sensor_alerts_flag_heat_and_stale_readings():
    reading = SimpleNamespace(
        sensor_type="temperature",
        value=40.5,
        unit="°C",
        timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    alerts = sensor_alert_messages(reading)

    assert (
        "warning",
        "Polyhouse temperature is high (40.5°C). Check ventilation and afternoon heat load.",
    ) in alerts
    assert (
        "warning",
        "temperature sensor data is stale. Check Home Assistant and sensor connectivity.",
    ) in alerts


def test_external_diagnosis_posts_image_with_context(monkeypatch, tmp_path):
    image_path = tmp_path / "leaf.jpg"
    image_path.write_bytes(b"fake image")

    class Response:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {"suggestions": [{"name": "Tomato"}]}

    def fake_post(url, headers, files, data, timeout):
        assert url == "http://plant-api.local/identify"
        assert headers == {"Api-Key": "secret"}
        assert "image" in files
        assert json.loads(data["context"]) == {"crop": "Tomato"}
        assert timeout == 45
        return Response()

    monkeypatch.setattr("services.external_diagnosis_client.httpx.post", fake_post)
    monkeypatch.setattr(
        "services.external_diagnosis_client.settings.plant_identification_api_url",
        "http://plant-api.local/identify",
    )
    monkeypatch.setattr(
        "services.external_diagnosis_client.settings.plant_identification_api_key",
        "secret",
    )

    result = ExternalDiagnosisClient("plant").diagnose(image_path, {"crop": "Tomato"})

    assert result == {
        "status": "ok",
        "provider_status_code": 200,
        "result": {"suggestions": [{"name": "Tomato"}]},
    }
