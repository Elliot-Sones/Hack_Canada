"""Add uploaded_documents and document_pages tables.

Revision ID: 003
Revises: 002
Create Date: 2026-03-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSON, UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uploaded_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("development_plans.id"), nullable=True),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("content_type", sa.String(200), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="uploaded"),
        sa.Column("doc_category", sa.String(100), nullable=True),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("extracted_data", JSON, nullable=True),
        sa.Column("compliance_findings", JSON, nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("ai_model", sa.String(100), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "document_pages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("uploaded_documents.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("page_number", sa.Integer, nullable=False),
        sa.Column("object_key", sa.String(500), nullable=False),
        sa.Column("width_px", sa.Integer, nullable=True),
        sa.Column("height_px", sa.Integer, nullable=True),
        sa.Column("extracted_text", sa.Text, nullable=True),
        sa.Column("analysis", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("document_pages")
    op.drop_table("uploaded_documents")
