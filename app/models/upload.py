import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class UploadedDocument(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "uploaded_documents"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("development_plans.id"), nullable=True
    )

    # File metadata
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(200), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Processing state
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded", server_default="uploaded")
    doc_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI analysis results
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    compliance_findings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_model: Mapped[str | None] = mapped_column(String(100), nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    pages: Mapped[list["DocumentPage"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentPage.page_number"
    )


class DocumentPage(Base, UUIDPrimaryKey, TimestampMixin):
    __tablename__ = "document_pages"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    width_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_px: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationship
    document: Mapped["UploadedDocument"] = relationship(back_populates="pages")
