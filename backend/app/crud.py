import json
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app import models, schemas


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
    alert = models.Alert(**payload.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


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
