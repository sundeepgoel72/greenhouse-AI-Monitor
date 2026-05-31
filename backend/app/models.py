from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Bed(Base):
    __tablename__ = "beds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    crop: Mapped[str | None] = mapped_column(String(120), nullable=True)
    sowing_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    transplant_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    polygon_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="bed", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="bed", cascade="all, delete-orphan"
    )
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="bed", cascade="all, delete-orphan"
    )


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    image_path: Mapped[str] = mapped_column(Text, nullable=False)

    metrics: Mapped[list["Metric"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), nullable=False, index=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("snapshots.id"), nullable=False, index=True
    )
    green_pct: Mapped[float] = mapped_column(Float, nullable=False)
    yellow_pct: Mapped[float] = mapped_column(Float, nullable=False)
    soil_pct: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    bed: Mapped[Bed] = relationship(back_populates="metrics")
    snapshot: Mapped[Snapshot] = relationship(back_populates="metrics")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    bed: Mapped[Bed] = relationship(back_populates="alerts")


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bed_id: Mapped[int] = mapped_column(ForeignKey("beds.id"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False, index=True
    )

    bed: Mapped[Bed] = relationship(back_populates="observations")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bed_id: Mapped[int | None] = mapped_column(ForeignKey("beds.id"), nullable=True)
    sensor_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
