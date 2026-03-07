"""Add created_at to policy_versions.

Revision ID: 004
Revises: 003
Create Date: 2026-03-07
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("policy_versions")}
    if "created_at" not in columns:
        op.add_column(
            "policy_versions",
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("policy_versions")}
    if "created_at" in columns:
        op.drop_column("policy_versions", "created_at")
