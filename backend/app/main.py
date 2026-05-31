from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.config import settings
from app.database import get_db, init_db
from services.frigate_client import FrigateClient
from services.metrics_engine import SnapshotIngestionService


app = FastAPI(title="Greenhouse AI Monitor", version="0.1.0")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


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
) -> dict:
    reading = crud.create_sensor_reading(db, payload)
    return {"id": reading.id}
