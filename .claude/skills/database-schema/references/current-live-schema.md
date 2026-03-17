# Current Live Database Schema

> Captured 2026-03-16 from **Railway PostGIS-DB** (production).
> Neon projects (`arterial`, `ntangible-rag`, `ApplicationAI`) are legacy/unused.

## Production Database

| Property | Value |
|----------|-------|
| **Host** | `postgis-db.railway.internal` (private) / `turntable.proxy.rlwy.net:17320` (public) |
| **Database** | `railway` |
| **Engine** | PostgreSQL + PostGIS 3.5.2 |
| **Extensions** | plpgsql, postgis, postgis_tiger_geocoder, postgis_topology, uuid-ossp, fuzzystrmatch |
| **Tables** | 66 |
| **Notable**: No pgvector extension — vector embeddings not available in production DB |

---

## Row Counts

### Populated

| Table | Rows | Notes |
|-------|------|-------|
| parcels | 1,051,599 | Main anchor entity — all Toronto parcels (2x Neon) |
| parcel_zoning_assignments | 661,118 | Spatial zone-to-parcel links (populated, unlike Neon) |
| dataset_features | 14,251 | GIS overlay/zoning polygons |
| development_applications | 8,444 | CoA/ZBA/OPA precedent records |
| policy_clauses | 15 | Seed — curated MVP policy corpus |
| policy_applicability_rules | 15 | Seed |
| unit_types | 6 | Seed |
| source_snapshots | 5 | Seed |
| ingestion_jobs | 5 | Seed |
| policy_documents | 5 | Seed |
| policy_versions | 5 | Seed |
| massing_templates | 4 | Seed |
| dataset_layers | 3 | Seed |
| jurisdictions | 2 | Toronto + 1 other |
| financial_assumption_sets | 2 | Seed |
| user (Better Auth) | 1 | 1 registered user |
| account (Better Auth) | 1 | 1 auth account |

### Empty (0 rows) — 49 tables

**User/tenant**: users, organizations, workspace_members, projects, project_parcels, project_shares

**Pipeline**: scenario_runs, massings, layout_runs, financial_runs, entitlement_results, precedent_searches, precedent_matches, analysis_snapshot_manifests, snapshot_manifests, snapshot_manifest_items

**Documents**: development_plans, submission_documents, uploaded_documents, document_pages, export_jobs, application_documents, rationale_extracts

**Infrastructure**: pipeline_assets, electrical_assets, bridge_assets

**Fact tables** (migrated but not populated): parcel_current_facts, parcel_building_facts, parcel_constraint_facts, parcel_zoning_facts

**Other**: parcel_addresses, parcel_metrics, feature_to_parcel_links, market_comparables, building_permits, parse_artifacts, parser_versions, parse_runs, policy_references, policy_review_items, review_queue_items, refresh_schedules, audit_events, design_branches, design_versions

**Auth**: session, verification (Better Auth tables — no active sessions)

---

## Table Schemas

### Better Auth Tables (Railway-only)

#### `user` (1 row)

Better Auth managed table — camelCase columns, text IDs.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | text | NOT NULL | |
| name | text | NOT NULL | |
| email | text | NOT NULL | |
| emailVerified | boolean | NOT NULL | false |
| image | text | NULL | |
| createdAt | timestamptz | NOT NULL | now() |
| updatedAt | timestamptz | NOT NULL | now() |

- **UQ**: `(email)`

#### `account` (1 row)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | text | NOT NULL | |
| userId | text | NOT NULL | |
| accountId | text | NOT NULL | |
| providerId | text | NOT NULL | |
| accessToken | text | NULL | |
| refreshToken | text | NULL | |
| accessTokenExpiresAt | timestamptz | NULL | |
| refreshTokenExpiresAt | timestamptz | NULL | |
| scope | text | NULL | |
| idToken | text | NULL | |
| password | text | NULL | |
| createdAt | timestamptz | NOT NULL | now() |
| updatedAt | timestamptz | NOT NULL | now() |

#### `session` (0 rows)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | text | NOT NULL | |
| userId | text | NOT NULL | |
| token | text | NOT NULL | |
| expiresAt | timestamptz | NOT NULL | |
| ipAddress | text | NULL | |
| userAgent | text | NULL | |
| createdAt | timestamptz | NOT NULL | now() |
| updatedAt | timestamptz | NOT NULL | now() |

- **UQ**: `(token)`

#### `verification` (0 rows)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | text | NOT NULL | |
| identifier | text | NOT NULL | |
| value | text | NOT NULL | |
| expiresAt | timestamptz | NOT NULL | |
| createdAt | timestamptz | NOT NULL | now() |
| updatedAt | timestamptz | NOT NULL | now() |

---

### Infrastructure Asset Tables (Railway-only)

#### `pipeline_assets` (0 rows)

Water mains, storm sewers, sanitary sewers, gas lines.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| jurisdiction_id | uuid | NOT NULL | FK → jurisdictions |
| source_snapshot_id | uuid | NULL | FK → source_snapshots |
| asset_id | varchar | NOT NULL | |
| pipe_type | varchar(50) | NOT NULL | |
| material | varchar(50) | NULL | |
| diameter_mm | float8 | NULL | |
| install_year | integer | NULL | |
| depth_m | float8 | NULL | |
| slope_pct | float8 | NULL | |
| length_m | float8 | NULL | |
| location_desc | varchar | NULL | |
| status | varchar(20) | NULL | 'ACTIVE' |
| attributes_json | json | NOT NULL | '{}' |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |
| geom | geometry | NULL | |

- **IDX**: GiST on `geom`, btree on `asset_id`, `jurisdiction_id`, `source_snapshot_id`

#### `electrical_assets` (0 rows)

Power lines, substations.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| jurisdiction_id | uuid | NOT NULL | FK → jurisdictions |
| source_snapshot_id | uuid | NULL | FK → source_snapshots |
| asset_id | varchar | NOT NULL | |
| asset_type | varchar(50) | NOT NULL | |
| voltage_kv | float8 | NULL | |
| voltage_tier | varchar(50) | NULL | |
| operator | varchar | NULL | |
| name | varchar | NULL | |
| cables | integer | NULL | |
| source_system | varchar(20) | NULL | |
| attributes_json | json | NOT NULL | '{}' |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |
| geom | geometry | NULL | |

- **IDX**: GiST on `geom`, btree on `asset_id`, `jurisdiction_id`

#### `bridge_assets` (0 rows)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| jurisdiction_id | uuid | NOT NULL | FK → jurisdictions |
| source_snapshot_id | uuid | NULL | FK → source_snapshots |
| asset_id | varchar | NOT NULL | |
| bridge_type | varchar(50) | NOT NULL | |
| structure_type | varchar(50) | NULL | |
| span_m | float8 | NULL | |
| deck_width_m | float8 | NULL | |
| clearance_m | float8 | NULL | |
| year_built | integer | NULL | |
| condition_rating | varchar(50) | NULL | |
| road_name | varchar | NULL | |
| crossing_name | varchar | NULL | |
| attributes_json | json | NOT NULL | '{}' |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |
| geom | geometry | NULL | |
| geom_line | geometry | NULL | |

---

### Fact Tables (Railway-only, migrated but empty)

#### `parcel_current_facts` (0 rows)

Basic current parcel profile — one row per parcel.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parcel_id | uuid | NOT NULL | FK → parcels, UQ |
| jurisdiction_id | uuid | NOT NULL | FK → jurisdictions |
| active_snapshot_id | uuid | NULL | FK → source_snapshots |
| canonical_address | varchar | NULL | |
| pin | varchar | NULL | |
| lot_area_m2 | float8 | NULL | |
| lot_frontage_m | float8 | NULL | |
| lot_depth_m | float8 | NULL | |
| current_use | varchar | NULL | |
| zone_code | varchar | NULL | |
| updated_at | timestamptz | NULL | now() |

- **IDX**: btree on `parcel_id` (UQ), `jurisdiction_id`, `pin`, `zone_code`

#### `parcel_building_facts` (0 rows)

Existing built form summary.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parcel_id | uuid | NOT NULL | FK → parcels, UQ |
| building_count | integer | NOT NULL | 0 |
| total_building_footprint_m2 | float8 | NULL | |
| building_coverage_pct | float8 | NULL | |
| vacant_lot_flag | boolean | NOT NULL | false |
| underutilized_flag | boolean | NOT NULL | false |
| updated_at | timestamptz | NULL | now() |

#### `parcel_constraint_facts` (0 rows)

Hard constraint flags.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parcel_id | uuid | NOT NULL | FK → parcels, UQ |
| heritage_flag | boolean | NOT NULL | false |
| floodplain_flag | boolean | NOT NULL | false |
| ravine_flag | boolean | NOT NULL | false |
| overlay_count | integer | NOT NULL | 0 |
| floodplain_coverage_pct | float8 | NULL | |
| updated_at | timestamptz | NULL | now() |

#### `parcel_zoning_facts` (0 rows)

Actionable zoning answers.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parcel_id | uuid | NOT NULL | FK → parcels, UQ |
| primary_zone_code | varchar | NULL | |
| zone_family | varchar | NULL | |
| max_height_m | float8 | NULL | |
| max_storeys | integer | NULL | |
| max_fsi | float8 | NULL | |
| max_lot_coverage_pct | float8 | NULL | |
| permitted_use_groups_json | json | NULL | |
| warnings_json | json | NULL | |
| updated_at | timestamptz | NULL | now() |

- **IDX**: btree on `parcel_id` (UQ), `primary_zone_code`, `zone_family`

---

### Parser Traceability (Railway-only)

#### `parser_versions` (0 rows)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parser_name | varchar | NOT NULL | |
| domain | varchar | NOT NULL | |
| version | varchar | NOT NULL | |
| parser_type | varchar | NOT NULL | |
| config_json | json | NULL | |
| status | varchar | NOT NULL | 'active' |
| created_at | timestamptz | NULL | now() |

- **UQ**: `(parser_name, version)`

#### `parse_runs` (0 rows)

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parser_version_id | uuid | NOT NULL | FK → parser_versions |
| source_snapshot_id | uuid | NULL | |
| entity_type | varchar | NOT NULL | |
| entity_id | uuid | NULL | |
| status | varchar | NOT NULL | 'pending' |
| confidence | float8 | NULL | |
| validation_summary_json | json | NOT NULL | '{}' |
| output_artifact_id | uuid | NULL | |
| created_at | timestamptz | NULL | now() |

---

### Core Domain Tables (same as Neon but with more data)

#### `parcels` (1,051,599 rows)

Same schema as Neon. Key differences: **2x the rows** (1.05M vs 528K).

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| jurisdiction_id | uuid | NOT NULL | FK → jurisdictions |
| pin | text | NULL | |
| address | text | NULL | |
| lot_area_m2 | float8 | NULL | |
| lot_frontage_m | float8 | NULL | |
| lot_depth_m | float8 | NULL | |
| current_use | text | NULL | |
| assessed_value | numeric | NULL | |
| zone_code | text | NULL | |
| geom | geometry | NOT NULL | |
| geom_area_m2 | float8 | NULL | |
| source_snapshot_id | uuid | NULL | |
| created_at | timestamptz | NOT NULL | now() |
| updated_at | timestamptz | NOT NULL | now() |

- **UQ**: `(jurisdiction_id, pin, source_snapshot_id)`
- **IDX**: GiST on `geom`, GIN full-text on `address`, btree on `(jurisdiction_id, zone_code)`

#### `parcel_zoning_assignments` (661,118 rows)

Spatial zone-to-parcel links — **populated on Railway, empty on Neon**.

| Column | Type | Nullable | Default |
|--------|------|----------|---------|
| id | uuid | NOT NULL | uuid_generate_v4() |
| parcel_id | uuid | NOT NULL | FK → parcels |
| dataset_feature_id | uuid | NOT NULL | FK → dataset_features |
| source_snapshot_id | uuid | NOT NULL | FK → source_snapshots |
| zone_code | text | NOT NULL | |
| overlap_area_m2 | float8 | NULL | |
| assignment_method | text | NOT NULL | |
| is_primary | boolean | NOT NULL | false |
| created_at | timestamptz | NOT NULL | now() |

#### Remaining domain tables

These have the **same schema as Neon** (documented in detail there). Key tables:

- `jurisdictions` (2 rows) — id, name, province, country, timezone, bbox_geom
- `dataset_layers` (3 rows) — jurisdiction_id, name, layer_type, source_url, license_status
- `dataset_features` (14,251 rows) — dataset_layer_id, source_record_id, attributes_json, geom
- `development_applications` (8,444 rows) — app_number, app_type, status, decision, proposed_height/units/fsi, geom
- `policy_documents` (5 rows) → `policy_versions` (5 rows) → `policy_clauses` (15 rows)
- `policy_applicability_rules` (15 rows) — clause → zone/geometry/use applicability
- `organizations` (0 rows), `users` (0 rows), `workspace_members` (0 rows)
- `projects` (0 rows), `scenario_runs` (0 rows), `development_plans` (0 rows)
- All pipeline tables (massings, layouts, financials, entitlements, precedents): 0 rows
- All document tables (submission_documents, uploaded_documents, export_jobs): 0 rows

---

## Key Differences: Railway vs Neon (arterial)

| Aspect | Railway (production) | Neon arterial (legacy) |
|--------|---------------------|----------------------|
| **Tables** | 66 | 53 |
| **Parcels** | 1,051,599 | 528,685 |
| **Zoning assignments** | 661,118 | 0 |
| **Fact tables** | 4 tables (migrated, empty) | Not present |
| **Infrastructure tables** | pipeline_assets, electrical_assets, bridge_assets | Not present |
| **Parser traceability** | parser_versions, parse_runs | Not present |
| **Better Auth tables** | user, account, session, verification (1 user) | Not present |
| **pgvector** | Not installed | Installed (0.8.0) |
| **PostGIS version** | 3.5.2 | 3.5.0 |
| **fuzzystrmatch** | Installed | Not installed |

---

## What's Working vs What's Not

### Working
- 1M+ parcels with geometry — full Toronto coverage
- 661K spatial zoning assignments linking parcels ↔ zone polygons
- 14K GIS features (overlay polygons)
- 8.4K development applications (precedent data)
- Better Auth with 1 registered user
- Seed data for policies, templates, unit types, financial assumptions

### Schema exists but unpopulated
- **Fact tables** (parcel_current_facts, parcel_building_facts, parcel_constraint_facts, parcel_zoning_facts) — migrated, indexed, but 0 rows. Need a backfill job.
- **Infrastructure** (pipeline_assets, electrical_assets, bridge_assets) — tables ready, ingestion endpoints exist, data not loaded
- **User-facing pipeline** — no users, orgs, projects, plans, or generated documents yet
- **Provenance chain** — parser_versions, parse_runs, parse_artifacts, snapshot_manifests all empty

### Missing from target architecture
- `parcel_policy_facts` — not yet in schema
- `parcel_precedent_facts` — not yet in schema
- `parcel_opportunity_facts` — not yet in schema
- `parcel_search_index` — not yet in schema
- **No pgvector** — can't do in-database vector search without installing the extension

### Vector store situation
- Production DB has **no pgvector** — embedding columns from Neon schema don't exist here
- ChromaDB (`fine-tuned-RAG/chroma_db/`) is the only active vector store
- Neon `ntangible-rag` has 54 knowledge_chunks with HNSW vector index — likely unused in production
