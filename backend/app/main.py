import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import SessionLocal, get_db, init_db
from services.frigate_client import FrigateClient
from services.external_diagnosis_client import ExternalDiagnosisClient
from services.home_assistant_client import HomeAssistantClient
from services.metrics_engine import SnapshotIngestionService
from services.sensor_alerts import create_sensor_alerts
from diagnostics.context_builder import build_context


app = FastAPI(title="Greenhouse AI Monitor", version="0.1.0")
logger = logging.getLogger(__name__)
scheduled_ingest_task: asyncio.Task | None = None

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup() -> None:
    init_db()
    global scheduled_ingest_task
    if settings.scheduled_ingest_enabled and settings.analysis_interval_seconds > 0:
        scheduled_ingest_task = asyncio.create_task(scheduled_ingest_loop())


@app.on_event("shutdown")
async def shutdown() -> None:
    if scheduled_ingest_task:
        scheduled_ingest_task.cancel()
        try:
            await scheduled_ingest_task
        except asyncio.CancelledError:
            pass


async def scheduled_ingest_loop() -> None:
    while True:
        await asyncio.sleep(settings.analysis_interval_seconds)
        db = SessionLocal()
        try:
            SnapshotIngestionService(db).ingest_from_frigate(FrigateClient())
            logger.info("Scheduled Frigate ingestion completed")
        except Exception:
            logger.exception("Scheduled Frigate ingestion failed")
        try:
            if (
                settings.home_assistant_base_url
                and settings.home_assistant_token
                and settings.home_assistant_sensors.strip()
                and settings.home_assistant_sensors.strip() != "[]"
            ):
                count = len(ingest_home_assistant_sensor_readings(db))
                logger.info("Scheduled Home Assistant sensor ingestion completed: %s", count)
        except Exception:
            logger.exception("Scheduled Home Assistant sensor ingestion failed")
        finally:
            db.close()


def snapshot_out(snapshot: models.Snapshot) -> schemas.SnapshotOut:
    return schemas.SnapshotOut(
        id=snapshot.id,
        timestamp=snapshot.timestamp,
        image_path=snapshot.image_path,
        image_url=f"/api/snapshots/{snapshot.id}/image",
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/config", response_model=schemas.UiConfigOut)
def ui_config() -> schemas.UiConfigOut:
    return schemas.UiConfigOut(
        alert_sensor_stale_minutes=settings.alert_sensor_stale_minutes,
    )


@app.get("/api/beds", response_model=list[schemas.BedOut])
def list_beds(db: Session = Depends(get_db)) -> list[schemas.BedOut]:
    return [crud.bed_to_schema(bed) for bed in crud.list_beds(db)]


@app.post("/api/beds", response_model=schemas.BedOut)
def create_bed(payload: schemas.BedCreate, db: Session = Depends(get_db)) -> schemas.BedOut:
    bed = crud.create_bed(db, payload)
    return crud.bed_to_schema(bed)


@app.get("/api/beds/{bed_id}", response_model=schemas.BedOut)
def get_bed(bed_id: int, db: Session = Depends(get_db)) -> schemas.BedOut:
    bed = crud.get_bed(db, bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return crud.bed_to_schema(bed)


@app.put("/api/beds/{bed_id}", response_model=schemas.BedOut)
def update_bed(
    bed_id: int, payload: schemas.BedUpdate, db: Session = Depends(get_db)
) -> schemas.BedOut:
    bed = crud.get_bed(db, bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    return crud.bed_to_schema(crud.update_bed(db, bed, payload))


@app.get("/api/snapshots", response_model=list[schemas.SnapshotOut])
def list_snapshots(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[schemas.SnapshotOut]:
    return [snapshot_out(snapshot) for snapshot in crud.list_snapshots(db, limit)]


@app.get("/api/snapshots/latest", response_model=schemas.SnapshotOut | None)
def latest_snapshot(db: Session = Depends(get_db)) -> schemas.SnapshotOut | None:
    snapshot = crud.get_latest_snapshot(db)
    return snapshot_out(snapshot) if snapshot else None


@app.get("/api/snapshots/{snapshot_id}/image")
def get_snapshot_image(snapshot_id: int, db: Session = Depends(get_db)) -> FileResponse:
    snapshot = db.get(models.Snapshot, snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    path = Path(snapshot.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Snapshot file not found")
    return FileResponse(path)


@app.post("/api/ingest/frigate", response_model=schemas.IngestionResult)
def ingest_frigate(db: Session = Depends(get_db)) -> schemas.IngestionResult:
    service = SnapshotIngestionService(db)
    snapshot, metrics, alerts = service.ingest_from_frigate(FrigateClient())
    return schemas.IngestionResult(
        snapshot=snapshot_out(snapshot),
        metrics=[schemas.MetricOut.model_validate(metric) for metric in metrics],
        alerts=[schemas.AlertOut.model_validate(alert) for alert in alerts],
    )


@app.post("/api/ingest/upload", response_model=schemas.IngestionResult)
def ingest_upload(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> schemas.IngestionResult:
    service = SnapshotIngestionService(db)
    snapshot, metrics, alerts = service.ingest_upload(image)
    return schemas.IngestionResult(
        snapshot=snapshot_out(snapshot),
        metrics=[schemas.MetricOut.model_validate(metric) for metric in metrics],
        alerts=[schemas.AlertOut.model_validate(alert) for alert in alerts],
    )


@app.get("/api/metrics", response_model=list[schemas.MetricOut])
def list_metrics(
    bed_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[schemas.MetricOut]:
    return [
        schemas.MetricOut.model_validate(metric)
        for metric in crud.list_metrics(db, bed_id=bed_id, limit=limit)
    ]


@app.get("/api/beds/{bed_id}/metrics/history", response_model=list[schemas.MetricHistoryOut])
def metric_history(
    bed_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[schemas.MetricHistoryOut]:
    if not crud.get_bed(db, bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")
    return [
        schemas.MetricHistoryOut(
            id=metric.id,
            bed_id=metric.bed_id,
            snapshot_id=metric.snapshot_id,
            snapshot_timestamp=timestamp,
            green_pct=metric.green_pct,
            yellow_pct=metric.yellow_pct,
            soil_pct=metric.soil_pct,
            created_at=metric.created_at,
        )
        for metric, timestamp in crud.list_metric_history(db, bed_id=bed_id, limit=limit)
    ]


@app.get("/api/alerts", response_model=list[schemas.AlertOut])
def list_alerts(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
) -> list[schemas.AlertOut]:
    return [schemas.AlertOut.model_validate(alert) for alert in crud.list_alerts(db, limit)]


@app.post("/api/alerts", response_model=schemas.AlertOut)
def create_alert(
    payload: schemas.AlertCreate, db: Session = Depends(get_db)
) -> schemas.AlertOut:
    if not crud.get_bed(db, payload.bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")
    return schemas.AlertOut.model_validate(crud.create_alert(db, payload))


@app.get("/api/observations", response_model=list[schemas.ObservationOut])
def list_observations(
    limit: int = Query(default=100, ge=1, le=500), db: Session = Depends(get_db)
) -> list[schemas.ObservationOut]:
    return [
        schemas.ObservationOut.model_validate(observation)
        for observation in crud.list_observations(db, limit)
    ]


@app.post("/api/observations", response_model=schemas.ObservationOut)
def create_observation(
    payload: schemas.ObservationCreate, db: Session = Depends(get_db)
) -> schemas.ObservationOut:
    if not crud.get_bed(db, payload.bed_id):
        raise HTTPException(status_code=404, detail="Bed not found")
    return schemas.ObservationOut.model_validate(crud.create_observation(db, payload))


@app.post("/api/sensor-readings")
def create_sensor_reading(
    payload: schemas.SensorReadingCreate, db: Session = Depends(get_db)
) -> schemas.SensorReadingOut:
    reading = crud.create_sensor_reading(db, payload)
    create_sensor_alerts(db, reading)
    return schemas.SensorReadingOut.model_validate(reading)


@app.get("/api/sensor-readings", response_model=list[schemas.SensorReadingOut])
def list_sensor_readings(
    sensor_type: str | None = None,
    bed_id: int | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[schemas.SensorReadingOut]:
    return [
        schemas.SensorReadingOut.model_validate(reading)
        for reading in crud.list_sensor_readings(
            db, sensor_type=sensor_type, bed_id=bed_id, limit=limit
        )
    ]


@app.post("/api/sensor-readings/home-assistant", response_model=list[schemas.SensorReadingOut])
def ingest_home_assistant_sensors(
    db: Session = Depends(get_db),
) -> list[schemas.SensorReadingOut]:
    try:
        readings = ingest_home_assistant_sensor_readings(db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [schemas.SensorReadingOut.model_validate(reading) for reading in readings]


def ingest_home_assistant_sensor_readings(db: Session) -> list[models.SensorReading]:
    try:
        client = HomeAssistantClient()
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    readings = []
    for payload in client.read_configured_sensors():
        reading = crud.create_sensor_reading(db, payload)
        create_sensor_alerts(db, reading)
        readings.append(reading)
    return readings


@app.post("/api/diagnostics/external")
def external_diagnosis(
    kind: Literal["plant", "disease"] = Form(...),
    bed_id: int | None = Form(default=None),
    snapshot_id: int | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> dict:
    image_path = resolve_diagnosis_image(db, image=image, snapshot_id=snapshot_id)
    context = diagnosis_context(db, bed_id)
    try:
        return ExternalDiagnosisClient(kind).diagnose(image_path, context)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def resolve_diagnosis_image(
    db: Session,
    image: UploadFile | None,
    snapshot_id: int | None,
) -> Path:
    if image is not None:
        if not image.content_type or not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Upload must be an image")
        now = datetime.now()
        suffix = Path(image.filename or "diagnosis.jpg").suffix or ".jpg"
        out_dir = Path(settings.snapshot_dir) / "diagnostics" / now.strftime("%Y-%m-%d")
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f'{now.strftime("%H%M%S%f")}{suffix}'
        path.write_bytes(image.file.read())
        return path

    snapshot = db.get(models.Snapshot, snapshot_id) if snapshot_id else crud.get_latest_snapshot(db)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    path = Path(snapshot.image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Snapshot file not found")
    return path


def diagnosis_context(db: Session, bed_id: int | None) -> dict:
    if bed_id is None:
        return {}
    bed = crud.get_bed(db, bed_id)
    if not bed:
        raise HTTPException(status_code=404, detail="Bed not found")
    metrics = crud.list_metrics(db, bed_id=bed_id, limit=1)
    readings = crud.list_sensor_readings(db, limit=50)
    sensor_map = latest_sensor_context(readings)
    return build_context(
        crud.bed_to_schema(bed).model_dump(),
        schemas.MetricOut.model_validate(metrics[0]).model_dump() if metrics else {},
        sensor_map,
    )


def latest_sensor_context(readings: list[models.SensorReading]) -> dict:
    context = {}
    for reading in readings:
        sensor_type = reading.sensor_type.lower()
        if sensor_type == "temperature" and "temperature_c" not in context:
            context["temperature_c"] = reading.value
        elif sensor_type == "humidity" and "humidity_pct" not in context:
            context["humidity_pct"] = reading.value
        elif sensor_type == "lux" and "lux" not in context:
            context["lux"] = reading.value
        elif sensor_type == "soil_moisture" and "moisture_pct" not in context:
            context["moisture_pct"] = reading.value
    return context
