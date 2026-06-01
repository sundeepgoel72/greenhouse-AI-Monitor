from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings


def create_sensor_alerts(
    db: Session, reading: models.SensorReading
) -> list[models.Alert]:
    alerts: list[models.Alert] = []
    for severity, message in sensor_alert_messages(reading):
        for bed_id in target_bed_ids(db, reading):
            alerts.append(
                crud.create_alert(
                    db,
                    schemas.AlertCreate(
                        bed_id=bed_id,
                        severity=severity,
                        message=message,
                    ),
                )
            )
    return alerts


def sensor_alert_messages(reading: models.SensorReading) -> list[tuple[str, str]]:
    sensor_type = reading.sensor_type.lower()
    alerts: list[tuple[str, str]] = []

    if sensor_type == "temperature":
        if reading.value > settings.alert_temp_critical_above:
            alerts.append(
                (
                    "critical",
                    f"Polyhouse temperature is very high ({reading.value:.1f}{reading.unit or ''}). Increase ventilation, shade, or misting.",
                )
            )
        elif reading.value > settings.alert_temp_warning_above:
            alerts.append(
                (
                    "warning",
                    f"Polyhouse temperature is high ({reading.value:.1f}{reading.unit or ''}). Check ventilation and afternoon heat load.",
                )
            )

    if sensor_type == "humidity":
        if reading.value < settings.alert_humidity_warning_below:
            alerts.append(
                (
                    "warning",
                    f"Polyhouse humidity is low ({reading.value:.1f}{reading.unit or ''}). Check irrigation, misting, and ventilation.",
                )
            )
        elif reading.value > settings.alert_humidity_warning_above:
            alerts.append(
                (
                    "warning",
                    f"Polyhouse humidity is high ({reading.value:.1f}{reading.unit or ''}). Check ventilation and disease risk.",
                )
            )

    if is_stale(reading.timestamp):
        alerts.append(
            (
                "warning",
                f"{reading.sensor_type} sensor data is stale. Check Home Assistant and sensor connectivity.",
            )
        )

    return alerts


def target_bed_ids(db: Session, reading: models.SensorReading) -> list[int]:
    if reading.bed_id is not None:
        return [reading.bed_id]
    return [bed.id for bed in crud.list_beds(db)]


def is_stale(timestamp: datetime) -> bool:
    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    age = now - timestamp.astimezone(timezone.utc)
    return age.total_seconds() > settings.alert_sensor_stale_minutes * 60
