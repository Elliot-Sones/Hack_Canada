"""Materialized parcel fact tables for screening, ranking, and search."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKey


# ---------------------------------------------------------------------------
# 1. Parcel Current Facts — stable parcel profile for search & display
# ---------------------------------------------------------------------------

class ParcelCurrentFact(Base, UUIDPrimaryKey):
    __tablename__ = "parcel_current_facts"
    __table_args__ = (
        UniqueConstraint("parcel_id", name="uq_parcel_current_facts_parcel"),
    )

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"),
        nullable=False, index=True,
    )
    active_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_snapshots.id"),
        nullable=True,
    )
    canonical_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    pin: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    lot_area_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_frontage_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    lot_depth_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_use: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    zone_code: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    parcel = relationship("Parcel", foreign_keys=[parcel_id])


# ---------------------------------------------------------------------------
# 2. Parcel Building Facts — built-form condition for redevelopment screening
# ---------------------------------------------------------------------------

class ParcelBuildingFact(Base, UUIDPrimaryKey):
    __tablename__ = "parcel_building_facts"
    __table_args__ = (
        UniqueConstraint("parcel_id", name="uq_parcel_building_facts_parcel"),
    )

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    building_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_building_footprint_m2: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    building_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vacant_lot_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    underutilized_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    parcel = relationship("Parcel", foreign_keys=[parcel_id])


# ---------------------------------------------------------------------------
# 3. Parcel Constraint Facts — hard go/no-go/caution signals
# ---------------------------------------------------------------------------

class ParcelConstraintFact(Base, UUIDPrimaryKey):
    __tablename__ = "parcel_constraint_facts"
    __table_args__ = (
        UniqueConstraint("parcel_id", name="uq_parcel_constraint_facts_parcel"),
    )

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    heritage_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    floodplain_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    ravine_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    esa_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    overlay_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    floodplain_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    parcel = relationship("Parcel", foreign_keys=[parcel_id])


# ---------------------------------------------------------------------------
# 4. Parcel Zoning Facts — actionable zoning answers
# ---------------------------------------------------------------------------

class ParcelZoningFact(Base, UUIDPrimaryKey):
    __tablename__ = "parcel_zoning_facts"
    __table_args__ = (
        UniqueConstraint("parcel_id", name="uq_parcel_zoning_facts_parcel"),
    )

    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    primary_zone_code: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    zone_family: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    max_height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_storeys: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_fsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_lot_coverage_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    permitted_use_groups_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    warnings_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(),
    )

    parcel = relationship("Parcel", foreign_keys=[parcel_id])


# ---------------------------------------------------------------------------
# 5. Parser Versions + Parse Runs — parser traceability
# ---------------------------------------------------------------------------

class ParserVersion(Base, UUIDPrimaryKey):
    __tablename__ = "parser_versions"
    __table_args__ = (
        UniqueConstraint("parser_name", "version", name="uq_parser_versions_name_version"),
    )

    parser_name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String, nullable=False, index=True)
    version: Mapped[str] = mapped_column(String, nullable=False)
    parser_type: Mapped[str] = mapped_column(String, nullable=False)
    config_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parse_runs: Mapped[list["ParseRun"]] = relationship(back_populates="parser_version")


class ParseRun(Base, UUIDPrimaryKey):
    __tablename__ = "parse_runs"

    parser_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parser_versions.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    source_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_snapshots.id"),
        nullable=True, index=True,
    )
    entity_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending", server_default="pending")
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validation_summary_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    output_artifact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parse_artifacts.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parser_version: Mapped["ParserVersion"] = relationship(back_populates="parse_runs")
