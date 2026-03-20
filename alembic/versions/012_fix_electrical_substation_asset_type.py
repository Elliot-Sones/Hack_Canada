"""fix electrical substation asset_type: 'substation' -> 'electrical_substation'

Revision ID: 012
Revises: 011
Create Date: 2026-03-19

"""
from typing import Sequence, Union

from alembic import op


revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE electrical_assets SET asset_type = 'electrical_substation' WHERE asset_type = 'substation'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE electrical_assets SET asset_type = 'substation' WHERE asset_type = 'electrical_substation'"
    )
