import uuid
from datetime import datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDPrimaryKey


class DatasetLayer(Base, UUIDPrimaryKey):
    __tablename__ = "dataset_layers"
    __table_args__ = (
        UniqueConstraint("jurisdiction_id", "name", name="uq_dataset_layers_jurisdiction_name"),
    )

    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jurisdictions.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    layer_type: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    license_status: Mapped[str] = mapped_column(String, nullable=False, default="unknown", server_default="unknown")
    refresh_frequency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_refreshed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    features: Mapped[list["DatasetFeature"]] = relationship(back_populates="dataset_layer")


class DatasetFeature(Base, UUIDPrimaryKey):
    __tablename__ = "dataset_features"

    dataset_layer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_layers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_record_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    geom = mapped_column(Geometry("Geometry", srid=4326), nullable=False)
    attributes_json: Mapped[dict] = mapped_column(JSON, nullable=False, server_default="{}")
    effective_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dataset_layer: Mapped["DatasetLayer"] = relationship(back_populates="features")
    parcel_links: Mapped[list["FeatureToParcelLink"]] = relationship(back_populates="feature")


class FeatureToParcelLink(Base, UUIDPrimaryKey):
    __tablename__ = "feature_to_parcel_links"
    __table_args__ = (
        UniqueConstraint("feature_id", "parcel_id", "relationship_type", name="uq_feature_parcel_link"),
    )

    feature_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dataset_features.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parcel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        String, nullable=False, default="intersects", server_default="intersects"
    )

    feature: Mapped["DatasetFeature"] = relationship(back_populates="parcel_links")
