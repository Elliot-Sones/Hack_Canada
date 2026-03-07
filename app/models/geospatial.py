import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKey


class Jurisdiction(Base, UUIDPrimaryKey):
    __tablename__ = "jurisdictions"

    name: Mapped[str] = mapped_column(String, nullable=False)
    province: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False, default="CA", server_default="CA")
    bbox_geom = mapped_column(Geometry("Polygon", srid=4326), nullable=True)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="America/Toronto", server_default="America/Toronto")
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcels: Mapped[list["Parcel"]] = relationship(back_populates="jurisdiction")


class Parcel(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "parcels"
    __table_args__ = (
        UniqueConstraint("jurisdiction_id", "pin", name="uq_parcels_jurisdiction_pin"),
    )

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    pin: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    geom = mapped_column(Geometry("MultiPolygon", srid=4326), nullable=False)
    geom_area_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_area_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_frontage_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_depth_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_use: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assessed_value: Mapped[Optional[float]] = mapped_column(Numeric(14, 2), nullable=True)
    zone_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    jurisdiction: Mapped["Jurisdiction"] = relationship(back_populates="parcels")
    metrics: Mapped[list["ParcelMetric"]] = relationship(back_populates="parcel")


class ParcelMetric(Base, UUIDPrimaryKey):
    __tablename__ = "parcel_metrics"
    __table_args__ = (
        UniqueConstraint("parcel_id", "metric_type", name="uq_parcel_metrics_parcel_type"),
    )

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_type: Mapped[str] = mapped_column(String, nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parcel: Mapped["Parcel"] = relationship(back_populates="metrics")


class ProjectParcel(Base, UUIDPrimaryKey):
    __tablename__ = "project_parcels"
    __table_args__ = (
        UniqueConstraint("project_id", "parcel_id", name="uq_project_parcels_project_parcel"),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String, nullable=False, default="primary", server_default="primary")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
