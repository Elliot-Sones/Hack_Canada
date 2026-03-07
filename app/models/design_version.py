"""Design version control models — branches and versioned snapshots."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class DesignBranch(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "design_branches"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    versions: Mapped[list["DesignVersion"]] = relationship(
        back_populates="branch", cascade="all, delete-orphan", order_by="DesignVersion.version_number"
    )


class DesignVersion(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "design_versions"

    branch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_branches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("design_versions.id"), nullable=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Geometry snapshot
    floor_plans: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_params: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Compliance snapshot
    compliance_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown", server_default="unknown"
    )
    compliance_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    variance_items: Mapped[list | None] = mapped_column(JSON, nullable=True)
    blocking_issues: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Metadata
    message: Mapped[str] = mapped_column(Text, nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Relationships
    branch: Mapped["DesignBranch"] = relationship(back_populates="versions")
