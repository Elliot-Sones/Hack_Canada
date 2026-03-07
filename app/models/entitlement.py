import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDPrimaryKey


class EntitlementResult(Base, UUIDPrimaryKey):
    __tablename__ = "entitlement_results"

    scenario_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    overall_compliance: Mapped[str] = mapped_column(String, nullable=False)
    result_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PrecedentSearch(Base, UUIDPrimaryKey):
    __tablename__ = "precedent_searches"

    scenario_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    search_params_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    results_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DevelopmentApplication(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "development_applications"
    __table_args__ = (
        UniqueConstraint("jurisdiction_id", "app_number", name="uq_dev_apps_jurisdiction_app"),
    )

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False, index=True
    )
    app_number: Mapped[str] = mapped_column(String, nullable=False, index=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parcel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True, index=True
    )
    geom = mapped_column(Geometry("Point", srid=4326), nullable=True)
    app_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    decision: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    decision_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    proposed_height_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    proposed_units: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    proposed_fsi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    proposed_use: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")

    documents: Mapped[list["ApplicationDocument"]] = relationship(back_populates="application")


class ApplicationDocument(Base, UUIDPrimaryKey):
    __tablename__ = "application_documents"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("development_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String, nullable=False)
    object_key: Mapped[str] = mapped_column(String, nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped["DevelopmentApplication"] = relationship(back_populates="documents")
    rationale_extracts: Mapped[list["RationaleExtract"]] = relationship(back_populates="application_document")


class RationaleExtract(Base, UUIDPrimaryKey):
    __tablename__ = "rationale_extracts"

    application_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("application_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    extract_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    embedding = mapped_column(Vector(384), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application_document: Mapped["ApplicationDocument"] = relationship(back_populates="rationale_extracts")
