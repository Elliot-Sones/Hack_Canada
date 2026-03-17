"""add parcel fact tables and parser traceability

Revision ID: 4735abedb496
Revises: 009
Create Date: 2026-03-16 19:36:53.948940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = '4735abedb496'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. parser_versions
    op.create_table(
        'parser_versions',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('parser_name', sa.String(), nullable=False, index=True),
        sa.Column('domain', sa.String(), nullable=False, index=True),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('parser_type', sa.String(), nullable=False),
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('parser_name', 'version', name='uq_parser_versions_name_version'),
    )

    # 2. parcel_current_facts
    op.create_table(
        'parcel_current_facts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('parcel_id', UUID(as_uuid=True), sa.ForeignKey('parcels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('jurisdiction_id', UUID(as_uuid=True), sa.ForeignKey('jurisdictions.id'), nullable=False, index=True),
        sa.Column('active_snapshot_id', UUID(as_uuid=True), sa.ForeignKey('source_snapshots.id'), nullable=True),
        sa.Column('canonical_address', sa.String(), nullable=True),
        sa.Column('pin', sa.String(), nullable=True, index=True),
        sa.Column('lot_area_m2', sa.Float(), nullable=True),
        sa.Column('lot_frontage_m', sa.Float(), nullable=True),
        sa.Column('lot_depth_m', sa.Float(), nullable=True),
        sa.Column('current_use', sa.String(), nullable=True),
        sa.Column('zone_code', sa.String(), nullable=True, index=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('parcel_id', name='uq_parcel_current_facts_parcel'),
    )

    # 3. parcel_building_facts
    op.create_table(
        'parcel_building_facts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('parcel_id', UUID(as_uuid=True), sa.ForeignKey('parcels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('building_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_building_footprint_m2', sa.Float(), nullable=True),
        sa.Column('building_coverage_pct', sa.Float(), nullable=True),
        sa.Column('vacant_lot_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('underutilized_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('parcel_id', name='uq_parcel_building_facts_parcel'),
    )

    # 4. parcel_constraint_facts
    op.create_table(
        'parcel_constraint_facts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('parcel_id', UUID(as_uuid=True), sa.ForeignKey('parcels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('heritage_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('floodplain_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ravine_flag', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('overlay_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('floodplain_coverage_pct', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('parcel_id', name='uq_parcel_constraint_facts_parcel'),
    )

    # 5. parcel_zoning_facts
    op.create_table(
        'parcel_zoning_facts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('parcel_id', UUID(as_uuid=True), sa.ForeignKey('parcels.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('primary_zone_code', sa.String(), nullable=True, index=True),
        sa.Column('zone_family', sa.String(), nullable=True, index=True),
        sa.Column('max_height_m', sa.Float(), nullable=True),
        sa.Column('max_storeys', sa.Integer(), nullable=True),
        sa.Column('max_fsi', sa.Float(), nullable=True),
        sa.Column('max_lot_coverage_pct', sa.Float(), nullable=True),
        sa.Column('permitted_use_groups_json', sa.JSON(), nullable=True),
        sa.Column('warnings_json', sa.JSON(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('parcel_id', name='uq_parcel_zoning_facts_parcel'),
    )

    # 6. parse_runs
    op.create_table(
        'parse_runs',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('parser_version_id', UUID(as_uuid=True), sa.ForeignKey('parser_versions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('source_snapshot_id', UUID(as_uuid=True), sa.ForeignKey('source_snapshots.id'), nullable=True, index=True),
        sa.Column('entity_type', sa.String(), nullable=False, index=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('validation_summary_json', sa.JSON(), nullable=False, server_default='{}'),
        sa.Column('output_artifact_id', UUID(as_uuid=True), sa.ForeignKey('parse_artifacts.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('parse_runs')
    op.drop_table('parcel_zoning_facts')
    op.drop_table('parcel_constraint_facts')
    op.drop_table('parcel_building_facts')
    op.drop_table('parcel_current_facts')
    op.drop_table('parser_versions')
