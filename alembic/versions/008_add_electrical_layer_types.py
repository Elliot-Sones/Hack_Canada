"""Add electrical infrastructure layer types to dataset_layers check constraint.

Revision ID: 008
Revises: 007
Create Date: 2026-03-10
"""
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None

NEW_LAYER_TYPES = [
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
    # Water system layers
    "water_main_distribution",
    "water_main_transmission",
    "water_hydrant",
    "water_valve",
    "water_fitting",
    "parks_drinking_water",
    # Electrical layers
    "electrical_pole",
    "power_line",
    "electrical_substation",
]


def upgrade() -> None:
    op.drop_constraint(
        "chk_dataset_layers_layer_type",
        "dataset_layers",
        type_="check",
    )
    types_sql = ", ".join(f"'{t}'::text" for t in NEW_LAYER_TYPES)
    op.create_check_constraint(
        "chk_dataset_layers_layer_type",
        "dataset_layers",
        f"layer_type = ANY (ARRAY[{types_sql}])",
    )


def downgrade() -> None:
    op.drop_constraint(
        "chk_dataset_layers_layer_type",
        "dataset_layers",
        type_="check",
    )
    # Restore 007 types (without electrical)
    prev_types = [
        "zoning", "height_overlay", "setback_overlay", "transit",
        "heritage", "floodplain", "environmental", "road", "amenity",
        "demographic", "building_mass", "other",
        "water_main_distribution", "water_main_transmission",
        "water_hydrant", "water_valve", "water_fitting", "parks_drinking_water",
    ]
    types_sql = ", ".join(f"'{t}'::text" for t in prev_types)
    op.create_check_constraint(
        "chk_dataset_layers_layer_type",
        "dataset_layers",
        f"layer_type = ANY (ARRAY[{types_sql}])",
    )
