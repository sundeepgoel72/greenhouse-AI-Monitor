import json
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from services.frigate_client import FrigateClient
from services.mqtt_publisher import MqttPublisher


class MetricsEngine:
    def __init__(self):
        self.publisher = MqttPublisher()
        self.thresholds = ColorThresholds.from_settings()
        self.alert_thresholds = AlertThresholds.from_settings()

    def analyze_bed(self, image: np.ndarray, polygon: list[dict]) -> dict[str, float]:
        if len(polygon) < 3:
            return {"green_pct": 0.0, "yellow_pct": 0.0, "soil_pct": 0.0}

        points = np.array([[point["x"], point["y"]] for point in polygon], dtype=np.int32)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        roi_pixels = int(np.count_nonzero(mask))
        if roi_pixels == 0:
            return {"green_pct": 0.0, "yellow_pct": 0.0, "soil_pct": 0.0}

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, self.thresholds.green_lower, self.thresholds.green_upper)
        yellow_mask = cv2.inRange(
            hsv, self.thresholds.yellow_lower, self.thresholds.yellow_upper
        )
        soil_mask = cv2.inRange(hsv, self.thresholds.soil_lower, self.thresholds.soil_upper)

        green = int(np.count_nonzero(cv2.bitwise_and(green_mask, green_mask, mask=mask)))
        yellow = int(np.count_nonzero(cv2.bitwise_and(yellow_mask, yellow_mask, mask=mask)))
        soil = int(np.count_nonzero(cv2.bitwise_and(soil_mask, soil_mask, mask=mask)))

        return {
            "green_pct": round((green / roi_pixels) * 100, 2),
            "yellow_pct": round((yellow / roi_pixels) * 100, 2),
            "soil_pct": round((soil / roi_pixels) * 100, 2),
        }

    def process_results(self, analysis_results: list[dict]):
        for result in analysis_results:
            bed_id = result["bed_id"]
            self.publisher.publish_bed_metrics(bed_id, result)

    def generate_alerts(self, metric: models.Metric) -> list[tuple[str, str]]:
        alerts: list[tuple[str, str]] = []
        if metric.green_pct < self.alert_thresholds.green_critical_below:
            alerts.append(
                (
                    "critical",
                    "Canopy coverage is very low. Inspect irrigation, light exposure, and plant establishment.",
                )
            )
        elif metric.green_pct < self.alert_thresholds.green_warning_below:
            alerts.append(
                (
                    "warning",
                    "Canopy coverage is low. Check for growth lag, watering gaps, or shading.",
                )
            )

        if metric.yellow_pct > self.alert_thresholds.yellow_critical_above:
            alerts.append(
                (
                    "critical",
                    "Yellowing is elevated. Inspect for nutrient deficiency, water stress, or disease symptoms.",
                )
            )
        elif metric.yellow_pct > self.alert_thresholds.yellow_warning_above:
            alerts.append(
                (
                    "warning",
                    "Yellowing is above the watch threshold. Inspect leaves and recent fertilizer schedule.",
                )
            )

        if metric.soil_pct > self.alert_thresholds.soil_warning_above:
            alerts.append(
                (
                    "warning",
                    "Soil visibility is high. Check canopy development and moisture conditions.",
                )
            )
        return alerts


def _hsv_triplet(value: str, name: str) -> np.ndarray:
    parts = [part.strip() for part in value.split(",")]
    if len(parts) != 3:
        raise ValueError(f"{name} must contain three comma-separated HSV values")
    try:
        numbers = [int(part) for part in parts]
    except ValueError as exc:
        raise ValueError(f"{name} must contain integer HSV values") from exc
    if any(number < 0 or number > 255 for number in numbers):
        raise ValueError(f"{name} HSV values must be between 0 and 255")
    return np.array(numbers, dtype=np.uint8)


class ColorThresholds:
    def __init__(
        self,
        green_lower: np.ndarray,
        green_upper: np.ndarray,
        yellow_lower: np.ndarray,
        yellow_upper: np.ndarray,
        soil_lower: np.ndarray,
        soil_upper: np.ndarray,
    ):
        self.green_lower = green_lower
        self.green_upper = green_upper
        self.yellow_lower = yellow_lower
        self.yellow_upper = yellow_upper
        self.soil_lower = soil_lower
        self.soil_upper = soil_upper

    @classmethod
    def from_settings(cls) -> "ColorThresholds":
        return cls(
            green_lower=_hsv_triplet(settings.green_hsv_lower, "GREEN_HSV_LOWER"),
            green_upper=_hsv_triplet(settings.green_hsv_upper, "GREEN_HSV_UPPER"),
            yellow_lower=_hsv_triplet(settings.yellow_hsv_lower, "YELLOW_HSV_LOWER"),
            yellow_upper=_hsv_triplet(settings.yellow_hsv_upper, "YELLOW_HSV_UPPER"),
            soil_lower=_hsv_triplet(settings.soil_hsv_lower, "SOIL_HSV_LOWER"),
            soil_upper=_hsv_triplet(settings.soil_hsv_upper, "SOIL_HSV_UPPER"),
        )


class AlertThresholds:
    def __init__(
        self,
        green_critical_below: float,
        green_warning_below: float,
        yellow_critical_above: float,
        yellow_warning_above: float,
        soil_warning_above: float,
    ):
        self.green_critical_below = green_critical_below
        self.green_warning_below = green_warning_below
        self.yellow_critical_above = yellow_critical_above
        self.yellow_warning_above = yellow_warning_above
        self.soil_warning_above = soil_warning_above

    @classmethod
    def from_settings(cls) -> "AlertThresholds":
        return cls(
            green_critical_below=settings.alert_green_critical_below,
            green_warning_below=settings.alert_green_warning_below,
            yellow_critical_above=settings.alert_yellow_critical_above,
            yellow_warning_above=settings.alert_yellow_warning_above,
            soil_warning_above=settings.alert_soil_warning_above,
        )


class SnapshotIngestionService:
    def __init__(self, db: Session):
        self.db = db
        self.engine = MetricsEngine()

    def ingest_from_frigate(
        self, client: FrigateClient
    ) -> tuple[models.Snapshot, list[models.Metric], list[models.Alert]]:
        image_path, timestamp = client.save_latest(settings.snapshot_dir)
        return self._ingest_path(image_path, timestamp)

    def ingest_upload(
        self, upload: UploadFile
    ) -> tuple[models.Snapshot, list[models.Metric], list[models.Alert]]:
        if not upload.content_type or not upload.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Upload must be an image")
        now = datetime.now()
        suffix = Path(upload.filename or "snapshot.jpg").suffix or ".jpg"
        out_dir = Path(settings.snapshot_dir) / "uploads" / now.strftime("%Y-%m-%d")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f'{now.strftime("%H%M%S%f")}{suffix}'
        path.write_bytes(upload.file.read())
        return self._ingest_path(path, now)

    def _ingest_path(
        self, image_path: Path, timestamp: datetime
    ) -> tuple[models.Snapshot, list[models.Metric], list[models.Alert]]:
        image = cv2.imread(str(image_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Unable to decode snapshot image")

        snapshot = models.Snapshot(timestamp=timestamp, image_path=str(image_path))
        self.db.add(snapshot)
        self.db.flush()

        metrics: list[models.Metric] = []
        alerts: list[models.Alert] = []
        beds = self.db.query(models.Bed).order_by(models.Bed.id).all()
        for bed in beds:
            polygon = json.loads(bed.polygon_json or "[]")
            values = self.engine.analyze_bed(image, polygon)
            metric = models.Metric(
                bed_id=bed.id,
                snapshot_id=snapshot.id,
                green_pct=values["green_pct"],
                yellow_pct=values["yellow_pct"],
                soil_pct=values["soil_pct"],
            )
            self.db.add(metric)
            metrics.append(metric)
            if len(polygon) >= 3:
                for severity, message in self.engine.generate_alerts(metric):
                    alert = models.Alert(
                        bed_id=bed.id,
                        severity=severity,
                        message=message,
                    )
                    self.db.add(alert)
                    alerts.append(alert)

        self.db.commit()
        self.db.refresh(snapshot)
        for metric in metrics:
            self.db.refresh(metric)
            self.engine.publisher.publish_bed_metrics(
                metric.bed_id,
                {
                    "bed_id": metric.bed_id,
                    "snapshot_id": metric.snapshot_id,
                    "green_pct": metric.green_pct,
                    "yellow_pct": metric.yellow_pct,
                    "soil_pct": metric.soil_pct,
                    "snapshot_timestamp": snapshot.timestamp.isoformat(),
                    "created_at": metric.created_at.isoformat(),
                },
            )
        for alert in alerts:
            self.db.refresh(alert)
            self.engine.publisher.publish_bed_alert(
                alert.bed_id,
                {
                    "bed_id": alert.bed_id,
                    "severity": alert.severity,
                    "message": alert.message,
                    "created_at": alert.created_at.isoformat(),
                },
            )
        return snapshot, metrics, alerts
