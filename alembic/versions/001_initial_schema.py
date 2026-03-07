"""Initial schema — all tables, indexes, constraints.

Revision ID: 001
Revises:
Create Date: 2026-03-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # EXTENSIONS
    # =========================================================================
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "postgis"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # =========================================================================
    # 1. TENANT AND PROJECT MODEL
    # =========================================================================

    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("settings_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_organizations_slug", "organizations", ["slug"])

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_users_email", "users", ["email"])

    op.create_table(
        "workspace_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_workspace_members_org_user"),
    )
    op.execute(
        "ALTER TABLE workspace_members ADD CONSTRAINT chk_workspace_members_role "
        "CHECK (role IN ('owner', 'admin', 'analyst', 'viewer'))"
    )
    op.create_index("idx_workspace_members_org", "workspace_members", ["organization_id"])
    op.create_index("idx_workspace_members_user", "workspace_members", ["user_id"])

    op.create_table(
        "projects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE projects ADD CONSTRAINT chk_projects_status "
        "CHECK (status IN ('active', 'archived', 'deleted'))"
    )
    op.create_index("idx_projects_org", "projects", ["organization_id"])
    op.create_index("idx_projects_status", "projects", ["organization_id", "status"])

    op.create_table(
        "project_shares",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shared_with", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("permission", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "shared_with", name="uq_project_shares_project_user"),
    )
    op.execute(
        "ALTER TABLE project_shares ADD CONSTRAINT chk_project_shares_permission "
        "CHECK (permission IN ('view', 'edit', 'admin'))"
    )

    op.create_table(
        "scenario_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_scenario_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id"), nullable=True),
        sa.Column("scenario_type", sa.Text(), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("input_hash", sa.Text(), nullable=False),
        sa.Column("source_snapshot_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "ALTER TABLE scenario_runs ADD CONSTRAINT chk_scenario_runs_type "
        "CHECK (scenario_type IN ('base', 'variance', 'optimization'))"
    )
    op.execute(
        "ALTER TABLE scenario_runs ADD CONSTRAINT chk_scenario_runs_status "
        "CHECK (status IN ('pending', 'running', 'completed', 'failed'))"
    )
    op.create_index("idx_scenario_runs_project", "scenario_runs", ["project_id"])
    op.create_index("idx_scenario_runs_parent", "scenario_runs", ["parent_scenario_id"])
    op.create_index("idx_scenario_runs_input_hash", "scenario_runs", ["input_hash"])

    # =========================================================================
    # 2. JURISDICTIONS AND PARCELS
    # =========================================================================

    op.create_table(
        "jurisdictions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("province", sa.Text(), nullable=False),
        sa.Column("country", sa.Text(), nullable=False, server_default="CA"),
        sa.Column("timezone", sa.Text(), nullable=False, server_default="America/Toronto"),
        sa.Column("metadata_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    # Add geometry column via raw SQL for PostGIS
    op.execute(
        "ALTER TABLE jurisdictions ADD COLUMN bbox_geom geometry(Polygon, 4326)"
    )
    op.execute("CREATE INDEX idx_jurisdictions_bbox ON jurisdictions USING GIST (bbox_geom)")

    op.create_table(
        "parcels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("pin", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("lot_area_m2", sa.Float(), nullable=True),
        sa.Column("lot_frontage_m", sa.Float(), nullable=True),
        sa.Column("lot_depth_m", sa.Float(), nullable=True),
        sa.Column("current_use", sa.Text(), nullable=True),
        sa.Column("assessed_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("zone_code", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("jurisdiction_id", "pin", name="uq_parcels_jurisdiction_pin"),
    )
    # Add geometry column and computed column via raw SQL
    op.execute("ALTER TABLE parcels ADD COLUMN geom geometry(MultiPolygon, 4326) NOT NULL")
    op.execute(
        "ALTER TABLE parcels ADD COLUMN geom_area_m2 DOUBLE PRECISION "
        "GENERATED ALWAYS AS (ST_Area(geom::geography)) STORED"
    )
    op.execute("CREATE INDEX idx_parcels_geom ON parcels USING GIST (geom)")
    op.create_index("idx_parcels_jurisdiction", "parcels", ["jurisdiction_id"])
    op.create_index("idx_parcels_zone", "parcels", ["jurisdiction_id", "zone_code"])
    op.execute(
        "CREATE INDEX idx_parcels_address ON parcels USING GIN (to_tsvector('english', coalesce(address, '')))"
    )

    op.create_table(
        "parcel_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("parcel_id", UUID(as_uuid=True), sa.ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_type", sa.Text(), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("parcel_id", "metric_type", name="uq_parcel_metrics_parcel_type"),
    )
    op.create_index("idx_parcel_metrics_parcel", "parcel_metrics", ["parcel_id"])

    op.create_table(
        "project_parcels",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parcel_id", UUID(as_uuid=True), sa.ForeignKey("parcels.id"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="primary"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("project_id", "parcel_id", name="uq_project_parcels_project_parcel"),
    )
    op.execute(
        "ALTER TABLE project_parcels ADD CONSTRAINT chk_project_parcels_role "
        "CHECK (role IN ('primary', 'assembly', 'context'))"
    )

    # =========================================================================
    # 3. POLICY MODEL
    # =========================================================================

    op.create_table(
        "policy_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("doc_type", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.Text(), nullable=False),
        sa.Column("parse_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE policy_documents ADD CONSTRAINT chk_policy_documents_doc_type "
        "CHECK (doc_type IN ('zoning_bylaw', 'official_plan', 'secondary_plan', "
        "'design_guideline', 'amendment', 'site_specific', 'overlay', 'provincial_policy'))"
    )
    op.execute(
        "ALTER TABLE policy_documents ADD CONSTRAINT chk_policy_documents_parse_status "
        "CHECK (parse_status IN ('pending', 'parsing', 'parsed', 'failed', 'reviewed'))"
    )
    op.create_index("idx_policy_docs_jurisdiction", "policy_documents", ["jurisdiction_id"])
    op.create_index("idx_policy_docs_type", "policy_documents", ["jurisdiction_id", "doc_type"])
    op.create_index("idx_policy_docs_hash", "policy_documents", ["file_hash"])

    op.create_table(
        "policy_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("policy_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("parser_version", sa.Text(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("confidence_avg", sa.Float(), nullable=True),
        sa.Column("confidence_min", sa.Float(), nullable=True),
        sa.Column("clause_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("document_id", "version_number", name="uq_policy_versions_doc_version"),
    )
    op.execute(
        "CREATE INDEX idx_policy_versions_active ON policy_versions (document_id) WHERE is_active = true"
    )

    op.create_table(
        "policy_clauses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("policy_version_id", UUID(as_uuid=True), sa.ForeignKey("policy_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_ref", sa.Text(), nullable=False),
        sa.Column("page_ref", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_type", sa.Text(), nullable=False),
        sa.Column("normalized_json", JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE policy_clauses ADD CONSTRAINT chk_policy_clauses_confidence "
        "CHECK (confidence >= 0.0 AND confidence <= 1.0)"
    )
    # Add vector column via raw SQL
    op.execute("ALTER TABLE policy_clauses ADD COLUMN embedding vector(384)")
    op.create_index("idx_policy_clauses_version", "policy_clauses", ["policy_version_id"])
    op.create_index("idx_policy_clauses_type", "policy_clauses", ["normalized_type"])
    op.execute(
        "CREATE INDEX idx_policy_clauses_review ON policy_clauses (needs_review) WHERE needs_review = true"
    )
    op.execute(
        "CREATE INDEX idx_policy_clauses_embedding ON policy_clauses "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
    op.execute(
        "CREATE INDEX idx_policy_clauses_text ON policy_clauses "
        "USING GIN (to_tsvector('english', raw_text))"
    )

    op.create_table(
        "policy_references",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("from_clause_id", UUID(as_uuid=True), sa.ForeignKey("policy_clauses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_clause_id", UUID(as_uuid=True), sa.ForeignKey("policy_clauses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.Text(), nullable=False),
        sa.UniqueConstraint("from_clause_id", "to_clause_id", "relation_type", name="uq_policy_refs_from_to_type"),
    )
    op.execute(
        "ALTER TABLE policy_references ADD CONSTRAINT chk_policy_references_relation_type "
        "CHECK (relation_type IN ('amends', 'overrides', 'references', 'defines', 'exempts'))"
    )
    op.create_index("idx_policy_refs_from", "policy_references", ["from_clause_id"])
    op.create_index("idx_policy_refs_to", "policy_references", ["to_clause_id"])

    op.create_table(
        "policy_applicability_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("policy_clause_id", UUID(as_uuid=True), sa.ForeignKey("policy_clauses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("override_level", sa.Integer(), nullable=False),
        sa.Column("applicability_json", JSON(), nullable=False, server_default="{}"),
    )
    op.execute(
        "ALTER TABLE policy_applicability_rules ADD COLUMN geometry_filter geometry(MultiPolygon, 4326)"
    )
    op.execute(
        "ALTER TABLE policy_applicability_rules ADD COLUMN zone_filter TEXT[]"
    )
    op.execute(
        "ALTER TABLE policy_applicability_rules ADD COLUMN use_filter TEXT[]"
    )
    op.execute(
        "ALTER TABLE policy_applicability_rules ADD CONSTRAINT chk_applicability_override_level "
        "CHECK (override_level BETWEEN 1 AND 6)"
    )
    op.create_index("idx_applicability_clause", "policy_applicability_rules", ["policy_clause_id"])
    op.execute(
        "CREATE INDEX idx_applicability_geom ON policy_applicability_rules USING GIST (geometry_filter)"
    )
    op.execute(
        "CREATE INDEX idx_applicability_zone ON policy_applicability_rules USING GIN (zone_filter)"
    )

    # =========================================================================
    # 4. DATASET LAYERS
    # =========================================================================

    op.create_table(
        "dataset_layers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("layer_type", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("license_status", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("refresh_frequency", sa.Text(), nullable=True),
        sa.Column("last_refreshed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("jurisdiction_id", "name", name="uq_dataset_layers_jurisdiction_name"),
    )
    op.execute(
        "ALTER TABLE dataset_layers ADD CONSTRAINT chk_dataset_layers_layer_type "
        "CHECK (layer_type IN ('transit', 'heritage', 'floodplain', 'environmental', "
        "'road', 'amenity', 'demographic', 'building_mass', 'other'))"
    )
    op.execute(
        "ALTER TABLE dataset_layers ADD CONSTRAINT chk_dataset_layers_license_status "
        "CHECK (license_status IN ('open', 'restricted', 'licensed', 'unknown'))"
    )

    op.create_table(
        "dataset_features",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dataset_layer_id", UUID(as_uuid=True), sa.ForeignKey("dataset_layers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column("attributes_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("ALTER TABLE dataset_features ADD COLUMN geom geometry(Geometry, 4326) NOT NULL")
    op.create_index("idx_dataset_features_layer", "dataset_features", ["dataset_layer_id"])
    op.execute("CREATE INDEX idx_dataset_features_geom ON dataset_features USING GIST (geom)")

    op.create_table(
        "feature_to_parcel_links",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("feature_id", UUID(as_uuid=True), sa.ForeignKey("dataset_features.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parcel_id", UUID(as_uuid=True), sa.ForeignKey("parcels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.Text(), nullable=False, server_default="intersects"),
        sa.UniqueConstraint("feature_id", "parcel_id", "relationship_type", name="uq_feature_parcel_link"),
    )
    op.execute(
        "ALTER TABLE feature_to_parcel_links ADD CONSTRAINT chk_feature_parcel_relationship_type "
        "CHECK (relationship_type IN ('intersects', 'contains', 'within', 'adjacent'))"
    )
    op.create_index("idx_feature_parcel_feature", "feature_to_parcel_links", ["feature_id"])
    op.create_index("idx_feature_parcel_parcel", "feature_to_parcel_links", ["parcel_id"])

    # =========================================================================
    # 5. DEVELOPMENT APPLICATIONS AND PRECEDENTS
    # =========================================================================

    op.create_table(
        "development_applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("app_number", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("parcel_id", UUID(as_uuid=True), sa.ForeignKey("parcels.id"), nullable=True),
        sa.Column("app_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=True),
        sa.Column("proposed_height_m", sa.Float(), nullable=True),
        sa.Column("proposed_units", sa.Integer(), nullable=True),
        sa.Column("proposed_fsi", sa.Float(), nullable=True),
        sa.Column("proposed_use", sa.Text(), nullable=True),
        sa.Column("metadata_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("jurisdiction_id", "app_number", name="uq_dev_apps_jurisdiction_app"),
    )
    op.execute(
        "ALTER TABLE development_applications ADD COLUMN geom geometry(Point, 4326)"
    )
    op.execute(
        "ALTER TABLE development_applications ADD CONSTRAINT chk_dev_apps_decision "
        "CHECK (decision IN ('approved', 'refused', 'withdrawn', 'pending', 'appealed'))"
    )
    op.create_index("idx_dev_apps_jurisdiction", "development_applications", ["jurisdiction_id"])
    op.execute("CREATE INDEX idx_dev_apps_geom ON development_applications USING GIST (geom)")
    op.create_index("idx_dev_apps_parcel", "development_applications", ["parcel_id"])
    op.create_index("idx_dev_apps_decision", "development_applications", ["decision"])
    op.create_index("idx_dev_apps_type", "development_applications", ["app_type"])

    op.create_table(
        "application_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("application_id", UUID(as_uuid=True), sa.ForeignKey("development_applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doc_type", sa.Text(), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE application_documents ADD CONSTRAINT chk_app_docs_doc_type "
        "CHECK (doc_type IN ('staff_report', 'planning_rationale', 'drawings', 'data_sheet', 'decision_letter', 'other'))"
    )
    # Add vector column via raw SQL
    op.execute("ALTER TABLE application_documents ADD COLUMN embedding vector(384)")
    op.create_index("idx_app_docs_application", "application_documents", ["application_id"])
    op.execute(
        "CREATE INDEX idx_app_docs_embedding ON application_documents "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    op.create_table(
        "rationale_extracts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("application_document_id", UUID(as_uuid=True), sa.ForeignKey("application_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extract_type", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE rationale_extracts ADD CONSTRAINT chk_rationale_extracts_type "
        "CHECK (extract_type IN ('planning_rationale', 'staff_recommendation', 'condition', 'policy_reference', 'design_comment'))"
    )
    op.execute(
        "ALTER TABLE rationale_extracts ADD CONSTRAINT chk_rationale_extracts_confidence "
        "CHECK (confidence >= 0.0 AND confidence <= 1.0)"
    )
    # Add vector column via raw SQL
    op.execute("ALTER TABLE rationale_extracts ADD COLUMN embedding vector(384)")
    op.create_index("idx_rationale_doc", "rationale_extracts", ["application_document_id"])
    op.execute(
        "CREATE INDEX idx_rationale_embedding ON rationale_extracts "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # =========================================================================
    # 6. SIMULATION, MASSING, AND LAYOUT
    # =========================================================================

    op.create_table(
        "massing_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("typology", sa.Text(), nullable=False),
        sa.Column("parameters_json", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE massing_templates ADD CONSTRAINT chk_massing_templates_typology "
        "CHECK (typology IN ('tower', 'midrise', 'lowrise', 'townhouse', 'mixed', 'custom'))"
    )

    op.create_table(
        "massings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_run_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("massing_templates.id"), nullable=True),
        sa.Column("template_name", sa.Text(), nullable=True),
        sa.Column("geometry_3d_key", sa.Text(), nullable=True),
        sa.Column("total_gfa_m2", sa.Float(), nullable=True),
        sa.Column("total_gla_m2", sa.Float(), nullable=True),
        sa.Column("storeys", sa.Integer(), nullable=True),
        sa.Column("height_m", sa.Float(), nullable=True),
        sa.Column("lot_coverage_pct", sa.Float(), nullable=True),
        sa.Column("fsi", sa.Float(), nullable=True),
        sa.Column("summary_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("compliance_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("ALTER TABLE massings ADD COLUMN envelope_2d geometry(Polygon, 4326)")
    op.create_index("idx_massings_scenario", "massings", ["scenario_run_id"])

    op.create_table(
        "unit_types",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("bedroom_count", sa.Integer(), nullable=False),
        sa.Column("min_area_m2", sa.Float(), nullable=False),
        sa.Column("max_area_m2", sa.Float(), nullable=False),
        sa.Column("typical_area_m2", sa.Float(), nullable=False),
        sa.Column("min_width_m", sa.Float(), nullable=True),
        sa.Column("is_accessible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.execute(
        "ALTER TABLE unit_types ADD CONSTRAINT chk_unit_types_bedroom_count "
        "CHECK (bedroom_count >= 0)"
    )
    op.execute(
        "ALTER TABLE unit_types ADD CONSTRAINT chk_unit_types_area_range "
        "CHECK (min_area_m2 <= typical_area_m2 AND typical_area_m2 <= max_area_m2)"
    )

    op.create_table(
        "layout_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("massing_id", UUID(as_uuid=True), sa.ForeignKey("massings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False, server_default="max_revenue"),
        sa.Column("constraints_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("result_json", JSON(), nullable=True),
        sa.Column("total_units", sa.Integer(), nullable=True),
        sa.Column("total_area_m2", sa.Float(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "ALTER TABLE layout_runs ADD CONSTRAINT chk_layout_runs_objective "
        "CHECK (objective IN ('max_revenue', 'max_units', 'balanced', 'custom'))"
    )
    op.execute(
        "ALTER TABLE layout_runs ADD CONSTRAINT chk_layout_runs_status "
        "CHECK (status IN ('pending', 'running', 'completed', 'failed'))"
    )
    op.create_index("idx_layout_runs_massing", "layout_runs", ["massing_id"])

    # =========================================================================
    # 7. FINANCE
    # =========================================================================

    op.create_table(
        "market_comparables",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("comp_type", sa.Text(), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("license_status", sa.Text(), nullable=False, server_default="unknown"),
        sa.Column("attributes_json", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute("ALTER TABLE market_comparables ADD COLUMN geom geometry(Point, 4326)")
    op.execute(
        "ALTER TABLE market_comparables ADD CONSTRAINT chk_market_comps_type "
        "CHECK (comp_type IN ('rental', 'sale', 'land_sale', 'construction_cost'))"
    )
    op.create_index("idx_market_comps_jurisdiction", "market_comparables", ["jurisdiction_id"])
    op.create_index("idx_market_comps_type", "market_comparables", ["comp_type"])
    op.execute("CREATE INDEX idx_market_comps_geom ON market_comparables USING GIST (geom)")
    op.execute("CREATE INDEX idx_market_comps_date ON market_comparables (effective_date DESC)")

    op.create_table(
        "financial_assumption_sets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("assumptions_json", JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "financial_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_run_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assumption_set_id", UUID(as_uuid=True), sa.ForeignKey("financial_assumption_sets.id"), nullable=False),
        sa.Column("layout_run_id", UUID(as_uuid=True), sa.ForeignKey("layout_runs.id"), nullable=True),
        sa.Column("output_json", JSON(), nullable=False),
        sa.Column("total_revenue", sa.Numeric(14, 2), nullable=True),
        sa.Column("total_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("noi", sa.Numeric(14, 2), nullable=True),
        sa.Column("valuation", sa.Numeric(14, 2), nullable=True),
        sa.Column("residual_land_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("irr_pct", sa.Float(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_financial_runs_scenario", "financial_runs", ["scenario_run_id"])

    # =========================================================================
    # 8. ENTITLEMENT AND PRECEDENT
    # =========================================================================

    op.create_table(
        "entitlement_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_run_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_snapshot_id", UUID(as_uuid=True), nullable=True),
        sa.Column("overall_compliance", sa.Text(), nullable=False),
        sa.Column("result_json", JSON(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE entitlement_results ADD CONSTRAINT chk_entitlement_compliance "
        "CHECK (overall_compliance IN ('compliant', 'minor_variance', 'major_variance', 'non_compliant'))"
    )
    op.execute(
        "ALTER TABLE entitlement_results ADD CONSTRAINT chk_entitlement_score "
        "CHECK (score >= 0.0 AND score <= 1.0)"
    )
    op.create_index("idx_entitlement_results_scenario", "entitlement_results", ["scenario_run_id"])

    op.create_table(
        "precedent_searches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("scenario_run_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("search_params_json", JSON(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("results_json", JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_precedent_searches_scenario", "precedent_searches", ["scenario_run_id"])

    # =========================================================================
    # 9. EXPORTS AND AUDIT
    # =========================================================================

    op.create_table(
        "export_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scenario_run_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id"), nullable=True),
        sa.Column("export_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("object_key", sa.Text(), nullable=True),
        sa.Column("signed_url", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        "ALTER TABLE export_jobs ADD CONSTRAINT chk_export_jobs_type "
        "CHECK (export_type IN ('pdf', 'csv', 'xlsx', 'glb', 'obj', 'bundle'))"
    )
    op.execute(
        "ALTER TABLE export_jobs ADD CONSTRAINT chk_export_jobs_status "
        "CHECK (status IN ('pending', 'generating', 'completed', 'failed'))"
    )
    op.create_index("idx_export_jobs_project", "export_jobs", ["project_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("payload_json", JSON(), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_events_org", "audit_events", ["organization_id"])
    op.create_index("idx_audit_events_type", "audit_events", ["event_type"])
    op.execute("CREATE INDEX idx_audit_events_entity ON audit_events (entity_type, entity_id)")
    op.execute("CREATE INDEX idx_audit_events_created ON audit_events (created_at DESC)")

    # =========================================================================
    # 10. INGESTION AND SOURCE MANAGEMENT
    # =========================================================================

    op.create_table(
        "source_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("snapshot_type", sa.Text(), nullable=False),
        sa.Column("version_label", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("jurisdiction_id", "snapshot_type", "version_label", name="uq_source_snapshots_jurisdiction_type_label"),
    )
    op.execute(
        "CREATE INDEX idx_source_snapshots_active ON source_snapshots (jurisdiction_id, snapshot_type) WHERE is_active = true"
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("jurisdiction_id", UUID(as_uuid=True), sa.ForeignKey("jurisdictions.id"), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("records_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("records_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.execute(
        "ALTER TABLE ingestion_jobs ADD CONSTRAINT chk_ingestion_jobs_status "
        "CHECK (status IN ('pending', 'running', 'completed', 'failed', 'review_needed'))"
    )
    op.create_index("idx_ingestion_jobs_status", "ingestion_jobs", ["status"])
    op.create_index("idx_ingestion_jobs_jurisdiction", "ingestion_jobs", ["jurisdiction_id"])

    # =========================================================================
    # 11. DEVELOPMENT PLANS AND SUBMISSION DOCUMENTS
    # =========================================================================

    op.create_table(
        "development_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("scenario_run_id", UUID(as_uuid=True), sa.ForeignKey("scenario_runs.id"), nullable=True),
        sa.Column("original_query", sa.Text(), nullable=False),
        sa.Column("parsed_parameters", JSON(), nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("ai_model", sa.String(100), nullable=True),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("clarifications_needed", JSON(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("current_step", sa.String(100), nullable=True),
        sa.Column("pipeline_progress", JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_dev_plans_org", "development_plans", ["organization_id"])
    op.create_index("idx_dev_plans_created_by", "development_plans", ["created_by"])
    op.create_index("idx_dev_plans_status", "development_plans", ["status"])

    op.create_table(
        "submission_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("development_plans.id"), nullable=False),
        sa.Column("doc_type", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_json", JSON(), nullable=True),
        sa.Column("object_key", sa.String(500), nullable=True),
        sa.Column("ai_provider", sa.String(50), nullable=True),
        sa.Column("ai_model", sa.String(100), nullable=True),
        sa.Column("generation_prompt_hash", sa.String(64), nullable=True),
        sa.Column("format", sa.String(20), nullable=False, server_default="markdown"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_submission_docs_plan", "submission_documents", ["plan_id"])
    op.create_index("idx_submission_docs_type", "submission_documents", ["doc_type"])

    # =========================================================================
    # Add deferred FK: scenario_runs.source_snapshot_id -> source_snapshots.id
    # =========================================================================
    op.execute(
        "ALTER TABLE scenario_runs ADD CONSTRAINT fk_scenario_runs_source_snapshot "
        "FOREIGN KEY (source_snapshot_id) REFERENCES source_snapshots(id)"
    )
    op.execute(
        "ALTER TABLE entitlement_results ADD CONSTRAINT fk_entitlement_results_source_snapshot "
        "FOREIGN KEY (source_snapshot_id) REFERENCES source_snapshots(id)"
    )


def downgrade() -> None:
    # Drop deferred foreign keys first
    op.execute("ALTER TABLE entitlement_results DROP CONSTRAINT IF EXISTS fk_entitlement_results_source_snapshot")
    op.execute("ALTER TABLE scenario_runs DROP CONSTRAINT IF EXISTS fk_scenario_runs_source_snapshot")

    # Drop tables in reverse dependency order
    op.drop_table("submission_documents")
    op.drop_table("development_plans")
    op.drop_table("ingestion_jobs")
    op.drop_table("source_snapshots")
    op.drop_table("audit_events")
    op.drop_table("export_jobs")
    op.drop_table("precedent_searches")
    op.drop_table("entitlement_results")
    op.drop_table("financial_runs")
    op.drop_table("financial_assumption_sets")
    op.drop_table("market_comparables")
    op.drop_table("layout_runs")
    op.drop_table("unit_types")
    op.drop_table("massings")
    op.drop_table("massing_templates")
    op.drop_table("rationale_extracts")
    op.drop_table("application_documents")
    op.drop_table("development_applications")
    op.drop_table("feature_to_parcel_links")
    op.drop_table("dataset_features")
    op.drop_table("dataset_layers")
    op.drop_table("policy_applicability_rules")
    op.drop_table("policy_references")
    op.drop_table("policy_clauses")
    op.drop_table("policy_versions")
    op.drop_table("policy_documents")
    op.drop_table("project_parcels")
    op.drop_table("parcel_metrics")
    op.drop_table("parcels")
    op.drop_table("jurisdictions")
    op.drop_table("scenario_runs")
    op.drop_table("project_shares")
    op.drop_table("projects")
    op.drop_table("workspace_members")
    op.drop_table("users")
    op.drop_table("organizations")

    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "postgis"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
