"""Infrastructure data layer refactor.

- Add length_m, location_desc, status columns to pipeline_assets
- Add GIST spatial index on pipeline_assets.geom
- Create electrical_assets table with GIST index
- Remove infrastructure layer types from dataset_layers CHECK constraint
- Delete infrastructure rows from dataset_layers (cascades to dataset_features)

Revision ID: 009
Revises: 008
Create Date: 2026-03-11
"""

import sqlalchemy as sa
from alembic import op

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None

# Infrastructure layer types being removed from dataset_layers
INFRA_LAYER_TYPES = [
    "water_main_distribution",
    "water_main_transmission",
    "water_hydrant",
    "water_valve",
    "water_fitting",
    "parks_drinking_water",
    "electrical_pole",
    "power_line",
    "electrical_substation",
]

# Layer types that remain in dataset_layers (planning overlays only)
PLANNING_LAYER_TYPES = [
    "zoning",
    "height_overlay",
    "setback_overlay",
    "transit",
    "heritage",
    "floodplain",
    "environmental",
    "road",
    "amenity",
    "demographic",
    "building_mass",
    "other",
]


def upgrade() -> None:
    # ── 1. Add columns to pipeline_assets ──────────────────────────────────
    op.add_column("pipeline_assets", sa.Column("length_m", sa.Float, nullable=True))
    op.add_column("pipeline_assets", sa.Column("location_desc", sa.String, nullable=True))
    op.add_column(
        "pipeline_assets",
        sa.Column("status", sa.String(20), nullable=True, server_default="ACTIVE"),
    )

    # ── 2. GIST index on pipeline_assets.geom ──────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_pipeline_assets_geom "
        "ON pipeline_assets USING GIST (geom)"
    )

    # ── 3. Create electrical_assets table ──────────────────────────────────
    op.create_table(
        "electrical_assets",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "jurisdiction_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jurisdictions.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "source_snapshot_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_snapshots.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("asset_id", sa.String, nullable=False, index=True),
        sa.Column("asset_type", sa.String(50), nullable=False),
        sa.Column("voltage_kv", sa.Float, nullable=True),
        sa.Column("voltage_tier", sa.String(50), nullable=True),
        sa.Column("operator", sa.String, nullable=True),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("cables", sa.Integer, nullable=True),
        sa.Column("source_system", sa.String(20), nullable=True),
        sa.Column(
            "attributes_json",
            sa.dialects.postgresql.JSON,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # Add PostGIS Geometry column (generic — LineString for lines, Point for substations)
    op.execute(
        "SELECT AddGeometryColumn('electrical_assets', 'geom', 4326, 'GEOMETRY', 2)"
    )

    # GIST index on electrical_assets.geom
    op.execute(
        "CREATE INDEX idx_electrical_assets_geom "
        "ON electrical_assets USING GIST (geom)"
    )

    # ── 4. Clean up dataset_layers ─────────────────────────────────────────
    # Delete infrastructure rows (cascades to dataset_features via FK)
    types_list = ", ".join(f"'{t}'" for t in INFRA_LAYER_TYPES)
    op.execute(f"DELETE FROM dataset_layers WHERE layer_type IN ({types_list})")

    # Recreate CHECK constraint without infrastructure types
    op.drop_constraint("chk_dataset_layers_layer_type", "dataset_layers", type_="check")
    types_sql = ", ".join(f"'{t}'::text" for t in PLANNING_LAYER_TYPES)
    op.create_check_constraint(
        "chk_dataset_layers_layer_type",
        "dataset_layers",
        f"layer_type = ANY (ARRAY[{types_sql}])",
    )


def downgrade() -> None:
    # Restore CHECK constraint with all layer types
    op.drop_constraint("chk_dataset_layers_layer_type", "dataset_layers", type_="check")
    all_types = PLANNING_LAYER_TYPES + INFRA_LAYER_TYPES
    types_sql = ", ".join(f"'{t}'::text" for t in all_types)
    op.create_check_constraint(
        "chk_dataset_layers_layer_type",
        "dataset_layers",
        f"layer_type = ANY (ARRAY[{types_sql}])",
    )

    # Drop electrical_assets table
    op.drop_table("electrical_assets")

    # Remove new columns from pipeline_assets
    op.drop_index("idx_pipeline_assets_geom", table_name="pipeline_assets")
    op.drop_column("pipeline_assets", "status")
    op.drop_column("pipeline_assets", "location_desc")
    op.drop_column("pipeline_assets", "length_m")
