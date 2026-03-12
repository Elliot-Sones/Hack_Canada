"""Infrastructure asset models — pipelines (water, sewer, gas), electrical, and bridges."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, UUIDPrimaryKey


class PipelineAsset(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "pipeline_assets"

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    source_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_snapshots.id"), nullable=True, index=True
    )
    asset_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    pipe_type: Mapped[str] = mapped_column(String(50), nullable=False)
    material: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    diameter_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    install_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    depth_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    slope_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    location_desc: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, server_default="ACTIVE")
    geom = mapped_column(Geometry("LineString", srid=4326), nullable=True)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")


class ElectricalAsset(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "electrical_assets"

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    source_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_snapshots.id"), nullable=True, index=True
    )
    asset_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False)
    voltage_kv: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    voltage_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    operator: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cables: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_system: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    geom = mapped_column(Geometry("Geometry", srid=4326), nullable=True)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")


class BridgeAsset(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "bridge_assets"

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    source_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_snapshots.id"), nullable=True, index=True
    )
    asset_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    bridge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    structure_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    span_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    deck_width_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    clearance_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year_built: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    condition_rating: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    road_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    crossing_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    geom = mapped_column(Geometry("Point", srid=4326), nullable=True)
    geom_line = mapped_column(Geometry("LineString", srid=4326), nullable=True)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
