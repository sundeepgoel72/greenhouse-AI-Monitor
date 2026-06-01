import json
import re
from datetime import datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import settings


def bed_to_schema(bed: models.Bed) -> schemas.BedOut:
    return schemas.BedOut(
        id=bed.id,
        name=bed.name,
        crop=bed.crop,
        sowing_date=bed.sowing_date,
        transplant_date=bed.transplant_date,
        polygon=json.loads(bed.polygon_json or "[]"),
    )


def create_bed(db: Session, payload: schemas.BedCreate) -> models.Bed:
    bed = models.Bed(
        name=payload.name,
        crop=payload.crop,
        sowing_date=payload.sowing_date,
        transplant_date=payload.transplant_date,
        polygon_json=payload.model_dump_json(include={"polygon"}),
    )
    polygon = [point.model_dump() for point in payload.polygon]
    bed.polygon_json = json.dumps(polygon)
    db.add(bed)
    db.commit()
    db.refresh(bed)
    return bed


def update_bed(db: Session, bed: models.Bed, payload: schemas.BedUpdate) -> models.Bed:
    update = payload.model_dump(exclude_unset=True)
    if "polygon" in update:
        polygon = update.pop("polygon") or []
        bed.polygon_json = json.dumps(polygon)
    for key, value in update.items():
        setattr(bed, key, value)
    db.commit()
    db.refresh(bed)
    return bed


def get_bed(db: Session, bed_id: int) -> models.Bed | None:
    return db.get(models.Bed, bed_id)


def list_beds(db: Session) -> list[models.Bed]:
    return list(db.scalars(select(models.Bed).order_by(models.Bed.id)))


def get_latest_snapshot(db: Session) -> models.Snapshot | None:
    stmt = select(models.Snapshot).order_by(desc(models.Snapshot.timestamp)).limit(1)
    return db.scalar(stmt)


def list_snapshots(db: Session, limit: int = 20) -> list[models.Snapshot]:
    stmt = select(models.Snapshot).order_by(desc(models.Snapshot.timestamp)).limit(limit)
    return list(db.scalars(stmt))


def list_metrics(db: Session, bed_id: int | None = None, limit: int = 100) -> list[models.Metric]:
    stmt = select(models.Metric).order_by(desc(models.Metric.created_at)).limit(limit)
    if bed_id is not None:
        stmt = stmt.where(models.Metric.bed_id == bed_id)
    return list(db.scalars(stmt))


def list_metric_history(
    db: Session, bed_id: int, limit: int = 50
) -> list[tuple[models.Metric, datetime]]:
    stmt = (
        select(models.Metric, models.Snapshot.timestamp)
        .join(models.Snapshot, models.Snapshot.id == models.Metric.snapshot_id)
        .where(models.Metric.bed_id == bed_id)
        .order_by(desc(models.Snapshot.timestamp))
        .limit(limit)
    )
    rows = list(db.execute(stmt))
    rows.reverse()
    return [(metric, timestamp) for metric, timestamp in rows]


def create_observation(
    db: Session, payload: schemas.ObservationCreate
) -> models.Observation:
    observation = models.Observation(**payload.model_dump())
    db.add(observation)
    db.commit()
    db.refresh(observation)
    return observation


def list_observations(db: Session, limit: int = 100) -> list[models.Observation]:
    stmt = select(models.Observation).order_by(desc(models.Observation.created_at)).limit(limit)
    return list(db.scalars(stmt))


def create_alert(db: Session, payload: schemas.AlertCreate) -> models.Alert:
    existing = find_recent_duplicate_alert(db, payload)
    if existing:
        return existing
    alert = models.Alert(**payload.model_dump(), created_at=datetime.now())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def find_recent_duplicate_alert(
    db: Session, payload: schemas.AlertCreate
) -> models.Alert | None:
    if settings.alert_dedupe_minutes <= 0:
        return None
    cutoff = datetime.now() - timedelta(minutes=settings.alert_dedupe_minutes)
    stmt = (
        select(models.Alert)
        .where(
            models.Alert.bed_id == payload.bed_id,
            models.Alert.severity == payload.severity,
            models.Alert.created_at >= cutoff,
        )
        .order_by(desc(models.Alert.created_at))
    )
    fingerprint = alert_fingerprint(payload.message)
    for alert in db.scalars(stmt):
        if alert_fingerprint(alert.message) == fingerprint:
            return alert
    return None


def alert_fingerprint(message: str) -> str:
    normalized = re.sub(r"\([^)]*\)", "", message)
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return normalized


def list_alerts(db: Session, limit: int = 100) -> list[models.Alert]:
    stmt = select(models.Alert).order_by(desc(models.Alert.created_at)).limit(limit)
    return list(db.scalars(stmt))


def create_sensor_reading(
    db: Session, payload: schemas.SensorReadingCreate
) -> models.SensorReading:
    data = payload.model_dump()
    data["timestamp"] = data["timestamp"] or datetime.now()
    reading = models.SensorReading(**data)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def list_sensor_readings(
    db: Session,
    sensor_type: str | None = None,
    bed_id: int | None = None,
    limit: int = 100,
) -> list[models.SensorReading]:
    stmt = select(models.SensorReading).order_by(desc(models.SensorReading.timestamp)).limit(limit)
    if sensor_type is not None:
        stmt = stmt.where(models.SensorReading.sensor_type == sensor_type)
    if bed_id is not None:
        stmt = stmt.where(models.SensorReading.bed_id == bed_id)
    return list(db.scalars(stmt))
