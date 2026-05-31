from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)


class BedBase(BaseModel):
    name: str
    crop: str | None = None
    sowing_date: str | None = None
    transplant_date: str | None = None
    polygon: list[Point] = Field(default_factory=list)


class BedCreate(BedBase):
    pass


class BedUpdate(BaseModel):
    name: str | None = None
    crop: str | None = None
    sowing_date: str | None = None
    transplant_date: str | None = None
    polygon: list[Point] | None = None


class BedOut(BedBase):
    id: int

    model_config = {"from_attributes": True}


class SnapshotOut(BaseModel):
    id: int
    timestamp: datetime
    image_path: str
    image_url: str

    model_config = {"from_attributes": True}


class MetricOut(BaseModel):
    id: int
    bed_id: int
    snapshot_id: int
    green_pct: float
    yellow_pct: float
    soil_pct: float
    created_at: datetime

    model_config = {"from_attributes": True}


class AlertCreate(BaseModel):
    bed_id: int
    severity: Literal["info", "warning", "critical"] = "info"
    message: str


class AlertOut(AlertCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class IngestionResult(BaseModel):
    snapshot: SnapshotOut
    metrics: list[MetricOut]
    alerts: list[AlertOut] = Field(default_factory=list)


class ObservationCreate(BaseModel):
    bed_id: int
    kind: Literal["Watered", "Fertilized", "Pruned", "Harvested", "Note"]
    note: str | None = None


class ObservationOut(ObservationCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class SensorReadingCreate(BaseModel):
    bed_id: int | None = None
    sensor_type: str
    value: float
    unit: str | None = None
    timestamp: datetime | None = None
