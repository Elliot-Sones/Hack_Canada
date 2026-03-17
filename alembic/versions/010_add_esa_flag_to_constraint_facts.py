"""add esa_flag to parcel_constraint_facts

Revision ID: 010
Revises: 4735abedb496
Create Date: 2026-03-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '010'
down_revision: Union[str, None] = '4735abedb496'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'parcel_constraint_facts',
        sa.Column('esa_flag', sa.Boolean(), nullable=False, server_default='false'),
    )


def downgrade() -> None:
    op.drop_column('parcel_constraint_facts', 'esa_flag')
