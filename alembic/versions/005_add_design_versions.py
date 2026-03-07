"""Add design version control tables.

Revision ID: 005
Revises: 004
Create Date: 2026-03-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "design_branches",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "design_versions",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("branch_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("design_branches.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("parent_version_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("design_versions.id"), nullable=True),
        sa.Column("version_number", sa.Integer, nullable=False),
        sa.Column("floor_plans", sa.dialects.postgresql.JSON, nullable=True),
        sa.Column("model_params", sa.dialects.postgresql.JSON, nullable=True),
        sa.Column("compliance_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("compliance_details", sa.dialects.postgresql.JSON, nullable=True),
        sa.Column("variance_items", sa.dialects.postgresql.JSON, nullable=True),
        sa.Column("blocking_issues", sa.dialects.postgresql.JSON, nullable=True),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("change_summary", sa.Text, nullable=True),
        sa.Column("created_by", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Add floor plan columns to uploaded_documents
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("uploaded_documents")}
    if "page_classifications" not in columns:
        op.add_column("uploaded_documents", sa.Column("page_classifications", sa.dialects.postgresql.JSON, nullable=True))
    if "floor_plan_data" not in columns:
        op.add_column("uploaded_documents", sa.Column("floor_plan_data", sa.dialects.postgresql.JSON, nullable=True))


def downgrade() -> None:
    op.drop_table("design_versions")
    op.drop_table("design_branches")
    op.drop_column("uploaded_documents", "floor_plan_data")
    op.drop_column("uploaded_documents", "page_classifications")
