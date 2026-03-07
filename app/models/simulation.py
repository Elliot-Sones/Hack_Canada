import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKey


class MassingTemplate(Base, UUIDPrimaryKey):
    __tablename__ = "massing_templates"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    typology: Mapped[str] = mapped_column(String, nullable=False)
    parameters_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    massings: Mapped[list["Massing"]] = relationship(back_populates="template")


class Massing(Base, UUIDPrimaryKey):
    __tablename__ = "massings"

    scenario_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("massing_templates.id"), nullable=True
    )
    template_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    geometry_3d_key: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    envelope_2d = mapped_column(Geometry("Polygon", srid=4326), nullable=True)
    total_gfa_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_gla_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    storeys: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    compliance_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    template: Mapped[Optional["MassingTemplate"]] = relationship(back_populates="massings")
    layout_runs: Mapped[list["LayoutRun"]] = relationship(back_populates="massing")


class UnitType(Base, UUIDPrimaryKey):
    __tablename__ = "unit_types"

    jurisdiction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    bedroom_count: Mapped[int] = mapped_column(Integer, nullable=False)
    min_area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    max_area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    typical_area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    min_width_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_accessible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")


class LayoutRun(Base, UUIDPrimaryKey):
    __tablename__ = "layout_runs"

    massing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("massings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    objective: Mapped[str] = mapped_column(String, nullable=False, default="max_revenue", server_default="max_revenue")
    constraints_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    result_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    total_units: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_area_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    massing: Mapped["Massing"] = relationship(back_populates="layout_runs")
