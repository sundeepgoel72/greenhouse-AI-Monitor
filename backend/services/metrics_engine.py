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

    @staticmethod
    def analyze_bed(image: np.ndarray, polygon: list[dict]) -> dict[str, float]:
        if len(polygon) < 3:
            return {"green_pct": 0.0, "yellow_pct": 0.0, "soil_pct": 0.0}

        points = np.array([[point["x"], point["y"]] for point in polygon], dtype=np.int32)
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [points], 255)
        roi_pixels = int(np.count_nonzero(mask))
        if roi_pixels == 0:
            return {"green_pct": 0.0, "yellow_pct": 0.0, "soil_pct": 0.0}

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        green_mask = cv2.inRange(hsv, np.array([35, 35, 35]), np.array([90, 255, 255]))
        yellow_mask = cv2.inRange(hsv, np.array([18, 45, 45]), np.array([34, 255, 255]))
        soil_mask = cv2.inRange(hsv, np.array([5, 20, 20]), np.array([25, 210, 220]))

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

    @staticmethod
    def generate_alerts(metric: models.Metric) -> list[tuple[str, str]]:
        alerts: list[tuple[str, str]] = []
        if metric.green_pct < 15:
            alerts.append(
                (
                    "critical",
                    "Canopy coverage is very low. Inspect irrigation, light exposure, and plant establishment.",
                )
            )
        elif metric.green_pct < 30:
            alerts.append(
                (
                    "warning",
                    "Canopy coverage is low. Check for growth lag, watering gaps, or shading.",
                )
            )

        if metric.yellow_pct > 15:
            alerts.append(
                (
                    "critical",
                    "Yellowing is elevated. Inspect for nutrient deficiency, water stress, or disease symptoms.",
                )
            )
        elif metric.yellow_pct > 8:
            alerts.append(
                (
                    "warning",
                    "Yellowing is above the watch threshold. Inspect leaves and recent fertilizer schedule.",
                )
            )

        if metric.soil_pct > 65:
            alerts.append(
                (
                    "warning",
                    "Soil visibility is high. Check canopy development and moisture conditions.",
                )
            )
        return alerts


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
