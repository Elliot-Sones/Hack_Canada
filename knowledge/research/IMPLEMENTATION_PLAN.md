# Arterial Clone: Merged Implementation Plan

> Land-development due diligence platform — backend, data, policy, simulation, and infrastructure.

---

## 1. Context + Key Decisions + Toronto Data Sources

### Context

We are building a clone of [Arterial](https://www.arterial.design/) as a land-development due diligence platform. The focus is backend architecture, data pipelines, policy processing, simulation, and scalable infrastructure. UI is intentionally out of scope.

Arterial is best understood as five backend systems working together:

1. A geospatial parcel and map platform
2. A versioned policy and citation graph
3. A deterministic geometry and simulation engine
4. A precedent retrieval and entitlement scoring engine
5. A comparable-driven financial modeling engine

If we build only a zoning lookup or only a parcel search tool, we will miss the real value. The core of the product is the ability to turn a parcel into a defendable development scenario with citations, assumptions, geometry, and viability outputs.

### Key Decisions

| Decision | Choice |
|---|---|
| Scope | Single-city MVP: Toronto |
| Product focus | Backend-first, trustworthy policy resolution, scalable async analysis |
| Compliance philosophy | Deterministic rule engine is the source of truth |
| AI philosophy | LLMs for extraction, retrieval, summarization, and analyst assistance — never as final authority for legal compliance or geometry |
| Language | Python-first stack (FastAPI + workers) |
| Infrastructure | Docker Compose locally, Railway for MVP deploy, AWS/GCP growth path |
| Database | PostgreSQL 16 + PostGIS 3.4 + pgvector |
| Async | Celery (MVP) with migration path to Temporal |
| Search | OpenSearch for full-text; pgvector for semantic/vector search |

### Toronto Data Sources (with URLs)

#### Core Toronto Data

| Source | URL | Format | Notes |
|---|---|---|---|
| Zoning By-law 569-2013 (Map) | https://open.toronto.ca/dataset/zoning-by-law-569-2013-zoning-area-map/ | SHP / GeoJSON | Base zoning polygons, zone codes |
| Zoning By-law 569-2013 (Text) | https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/zoning-by-law-569-2013-2/ | HTML / PDF | Full bylaw text, amendments |
| Property Boundaries | https://open.toronto.ca/dataset/property-boundaries/ | SHP / GeoJSON | Cadastral parcel polygons |
| Address Points | https://open.toronto.ca/dataset/address-points-municipal-toronto-one-address-repository/ | SHP / CSV | Geocoding, parcel linkage |
| Development Applications | https://open.toronto.ca/dataset/development-applications/ | CSV / API | Application tracking, status, decisions |
| Building Permits (Active) | https://open.toronto.ca/dataset/building-permits-active-permits/ | CSV / API | Permits in progress |
| Building Permits (Cleared) | https://open.toronto.ca/dataset/building-permits-cleared-permits/ | CSV / API | Historical permits |
| Official Plan | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/ | PDF / HTML | Land use designations, policies |
| Secondary Plans | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/chapter-6-secondary-plans/ | PDF | Area-specific planning policies |
| Committee of Adjustment Decisions | https://open.toronto.ca/dataset/committee-of-adjustment-decisions/ | CSV | Minor variance decisions |
| Ontario Land Tribunal (OLT) | https://www.olt.gov.on.ca/decisions-and-orders/ | HTML / PDF | Appeal decisions |
| Toronto WMS/WFS Services | https://gis.toronto.ca/arcgis/rest/services | OGC WMS/WFS | GIS tile layers |

#### Enrichment Data

| Source | URL | Format | Notes |
|---|---|---|---|
| TTC Stops | https://open.toronto.ca/dataset/ttc-routes-and-schedules/ | GTFS | Transit proximity scoring |
| Heritage Register | https://open.toronto.ca/dataset/heritage-register/ | SHP / CSV | Heritage overlay constraints |
| Floodplain Mapping | https://trca.ca/conservation/flood-risk-management/flood-plain-map-viewer/ | WMS / SHP | TRCA flood constraints |
| Ravine & Natural Feature Protection | https://open.toronto.ca/dataset/ravine-and-natural-feature-protection/ | SHP | Environmental overlays |
| Neighbourhoods | https://open.toronto.ca/dataset/neighbourhoods/ | SHP / GeoJSON | Spatial context |
| Ward Boundaries | https://open.toronto.ca/dataset/city-wards/ | SHP | Governance context |
| 3D Massing Model | https://open.toronto.ca/dataset/3d-massing/ | 3D SHP / multipatch | Existing building mass |
| Road Centreline | https://open.toronto.ca/dataset/toronto-centreline-tcl/ | SHP | Frontage classification |
| Parks | https://open.toronto.ca/dataset/parks/ | SHP | Amenity context |

#### Licensed / Restricted Data (Requires Review)

| Source | Notes |
|---|---|
| MPAC Assessment Data | Property assessment values; redistribution restricted |
| MLS / TRREB Data | Sale and lease comps; strict licensing required |
| CoStar / Altus | Commercial comps and construction costs; subscription |
| CMHC Rental Market Reports | Vacancy, rent averages by zone; free but aggregated |
| Statistics Canada Census | Demographics; open but aggregated at tract level |

---

## 2. Executive Summary + Guiding Principles

### Executive Summary

Arterial is not just a parcel search tool and not just a zoning reader. It is a land-development decision engine that combines geospatial parcel discovery, policy ingestion, deterministic geometry simulation, layout optimization, financial modeling, precedent retrieval, and variance simulation into a single auditable workflow.

The backend therefore needs to behave like a combination of: GIS platform, policy knowledge graph, document processing pipeline, geometry engine, financial model service, search and recommendation engine, and long-running job orchestration system.

### Guiding Principles

#### 1. Deterministic beats plausible

Policy resolution, massing calculations, and financial computations must be reproducible. LLM output can help extract or rank information, but final answers need structured rules and deterministic evaluation.

#### 2. Every output must be explainable

Every result should separate: source facts, derived rule interpretations, simulation assumptions, and model predictions. This is essential for user trust, debugging, and enterprise adoption.

#### 3. Version everything

We must version: raw source files, parsed policy text, normalized rules, dataset refreshes, simulation inputs, model versions, and exported reports. If a user reruns the same scenario later, we should be able to explain why the output changed or prove that it did not.

#### 4. Async-first — design for long-running analysis

This product is not simple CRUD. OCR, parsing, massing, layout optimization, entitlement analysis, and report generation are all background jobs. The architecture must treat async work as a first-class concern from day one.

#### 5. Build a strong Toronto MVP before generalizing

Toronto is a good first city because the public data ecosystem is relatively strong. But the architecture should still assume that each future jurisdiction will have different terminology, source quality, and policy structure.

---

## 3. Product Modules + User Jobs + Primary Users

### Core Product Modules

| Module | Description |
|---|---|
| Policy Engine | Ingests, versions, structures, and resolves zoning bylaws, official plans, overlays, and regulations |
| Parcel Search | Finds and filters parcels by zoning, lot area, frontage, geometry, and opportunity criteria |
| Building Envelope / Massing | Generates as-of-right envelopes and candidate buildable forms from parcel geometry and policy constraints |
| Unit Mix & Layout Optimization | Allocates floor area across unit programs and tests layout assumptions |
| Financial Pro Forma | Estimates costs, revenue, NOI, valuation, and high-level returns |
| Entitlement Assessment | Compares a proposal against policy and comparable applications to estimate risk |
| Variance Simulation | Forks the scenario and tests what changes under requested policy overrides |
| Exports & Collaboration | Produces auditable reports, CSVs, spreadsheets, and 3D artifacts for teams |

### Core User Jobs to Be Done

1. Find parcels or sites worth analyzing.
2. Pull the full applicable policy stack for a site.
3. Determine what is allowed as-of-right.
4. Generate a buildable envelope and massing options.
5. Turn massing into unit/layout scenarios.
6. Estimate financial viability.
7. Review precedents and approval risk.
8. Export a shareable due diligence package.

### Primary Users

- Development analysts searching for opportunities
- Architects or planners testing form and compliance
- Acquisitions teams screening parcels at scale
- Entitlement consultants reviewing policy risk
- Real estate finance teams testing viability and returns
- Organization admins managing team data, permissions, and templates

---

## 4. Inputs & Outputs

### User Inputs

| Input | Type | Used By |
|---|---|---|
| Parcel address, coordinates, or PIN | Text / map / API | Parcel resolution, jurisdiction lookup, all downstream modules |
| Project boundary | Geometry or parcel set | Multi-parcel assembly and simulation |
| Development program | Structured form or API payload | Massing, layout, finance |
| Massing assumptions | Structured parameters (setbacks, stepbacks, height, cores, window wells, template) | Simulation engine |
| Policy overrides | Structured scenario inputs | Variance simulation |
| Search filters | Structured form | Parcel search and opportunity screening |
| Financial assumptions | Structured form (cap rate, expenses, vacancy, absorption, tenure) | Pro forma |
| Layout inputs | Unit types, area ranges, dimensional ranges, unit priorities, amenity constraints | Layout optimizer |
| Precedent search filters | Structured form or natural language prompt | Entitlement and precedent engine |
| Export preferences | Structured form | Report generation |
| Manual policy values | Structured input when jurisdiction data is incomplete | Policy overrides |

### User Outputs

| Output | Type | Module |
|---|---|---|
| Parcel summary | Structured JSON + site geometry | Geospatial service |
| Effective policy stack | Structured JSON + citations + source links | Policy engine |
| Applicable regulations | Clause list + normalized rules + source refs + effective dates | Policy engine |
| As-of-right envelope | Geometry + metrics + rule ranges | Simulation engine |
| Candidate massings | Geometry + metrics + assumptions + compliance deltas | Simulation engine |
| Unit mix scenarios | Structured tables + floor-plate options | Layout optimizer |
| Financial outputs | Structured metrics + assumptions + comp sets | Finance engine |
| Entitlement results | Rule-by-rule checks + pass/fail reasoning | Entitlement engine |
| Comparable precedents | Search results + approval outcomes + rationales | Precedent engine |
| Approval probability | Explainable score + feature breakdown | Precedent engine |
| Variance delta analysis | Before/after scenario comparison | Scenario engine |
| Export package | PDF / CSV / spreadsheet / 3D artifacts | Export service |

---

## 5. Result Explainability Model

Every analysis result uses a 4-layer explainability model:

### Layer 1: Source Fact

A verifiable datum from a published source with a citation chain.

Example: Zoning By-law 569-2013, Section 40.10.40.10 states a maximum building height of 36 metres for zone CR 3.0 (c2.0; r2.5) SS2.

### Layer 2: Derived Interpretation

A normalized, machine-readable rule extracted from the source fact.

Example: `{ "rule_type": "max_height", "value": 36.0, "unit": "m", "source_clause_id": "clause-4928", "confidence": 0.97 }`

### Layer 3: Simulation Assumption

A user-chosen or system-defaulted parameter used in computation.

Example: The user overrides height to 42 m for a tower massing scenario.

### Layer 4: Model Prediction

A probabilistic or scored output from an analytical model.

Example: Approval likelihood = 61% based on features: compliance_delta = -6m height, precedent_density = 4 approved within 500 m, district_similarity = 0.82.

### Why This Matters

If we keep these layers separate, the system remains explainable and debuggable. Users can trace any number back to its source. This prevents the platform from blending legal truth, analyst choices, and probabilistic outputs into one opaque number.

---

## 6. Functional Domains with Core Entities

### 1. Project and Tenant Domain

Responsibilities: organizations, users, workspaces, projects, project sharing, templates, audit history.

Core entities:
- `organization`
- `workspace_member`
- `project`
- `project_share`
- `scenario_run`
- `project_template`
- `audit_event`

### 2. Geospatial / Parcel and Map Domain

Responsibilities: address geocoding, parcel search, parcel geometry and adjacency, frontage/area/depth/lot characteristics, multi-parcel assembly, spatial overlays and jurisdiction lookup, map tile serving.

Core entities:
- `jurisdiction`
- `parcel`
- `parcel_geometry`
- `parcel_assessment`
- `parcel_jurisdiction`
- `parcel_metrics`
- `project_parcel`

### 3. Policy Domain

Responsibilities: ingest zoning bylaws, official plans, design guidelines, amendments, and planning bulletins; version policy documents by jurisdiction and effective date; extract clauses and cross-references; map policy clauses to normalized rule types; resolve applicable rules for a site and project type.

Core entities:
- `policy_document`
- `policy_version`
- `policy_clause`
- `policy_reference`
- `policy_applicability_rule`
- `project_policy_override`

### 4. Dataset Domain

Responsibilities: ingest polygon and point datasets; store lineage and source metadata; support dataset filtering and parcel overlays; expose development applications, permits, designations, demographics, transit, and market signals; refresh schedules.

Core entities:
- `dataset_layer`
- `dataset_feature`
- `dataset_refresh_job`
- `source_record`
- `feature_to_parcel_link`

### 5. Massing and Simulation Domain

Responsibilities: envelope generation, massing generation, scenario revisioning, compliance delta computation, deterministic geometry pipeline with explicit versioning.

Core entities:
- `massing`
- `massing_template`
- `massing_revision`
- `storey_profile`
- `reserved_space`
- `geometry_metric`

### 6. Layout Optimization Domain

Responsibilities: unit library and regional defaults, area-based and dimension-based unit simulation, floor-plate packing/allocation, equalization and floor-specific locking, revenue-aware optimization.

Core entities:
- `unit_type`
- `unit_mix`
- `floor_plate`
- `layout_run`
- `layout_candidate`

### 7. Finance Domain

Responsibilities: comparable rents and sales, construction costing, unit-level and project-level revenue projections, cap rate/NOI/valuation/return estimates, custom assumption overrides.

Core entities:
- `market_comparable`
- `construction_cost_model`
- `financial_assumption_set`
- `financial_run`
- `financial_output`

### 8. Entitlement and Precedent Domain

Responsibilities: compare project geometry to policy ranges, split objective legal checks from softer design-guideline checks, find comparable applications, interpret planning rationales, estimate approval probability.

Core entities:
- `entitlement_rule`
- `entitlement_run`
- `entitlement_result`
- `precedent_case`
- `precedent_search`
- `precedent_match`
- `rationale_extract`

### 9. Export and Collaboration Domain

Responsibilities: PDF reports, CSV exports, 3D exports, organization-scoped templates, sharing and permissions, auditable report generation, report versioning.

Core entities:
- `export_job`
- `report_template`
- `export_artifact`

### 10. Ingestion and Orchestration Domain

Responsibilities: scheduled source refreshes, parsing pipelines, validation workflows, publish new snapshots for online use, confidence scoring, human review routing.

Core entities:
- `ingestion_job`
- `source_snapshot`
- `parse_artifact`
- `review_queue_item`
- `refresh_schedule`

---

## 7. Data Requirements

### Core Source-of-Truth Data

- Cadastral parcel geometries (Property Boundaries dataset)
- Address and geocoder data (Address Points dataset)
- Zoning maps and zoning bylaws (By-law 569-2013 map + text)
- Official plan and secondary plan maps and text
- Urban design guidelines and built-form rules
- Area-specific guidelines
- Policy amendments and effective dates
- Site-specific exceptions and overlays
- Permitting and development application datasets
- Planning rationale documents, staff reports, and architectural attachments
- Committee of Adjustment and OLT decisions
- Parcel assessments and ownership where legally available

### Enrichment Data

- Transit stops and frequency (TTC GTFS)
- Amenities and neighborhood services
- Demographic and socioeconomic data (Census)
- Environmental constraints (Ravine protection)
- Floodplain and conservation overlays (TRCA)
- Heritage overlays (Heritage Register)
- School and infrastructure boundaries
- Road network and frontage context (Centreline)
- 3D existing building mass (3D Massing dataset)

### Metadata We Must Store for Every Source

| Field | Purpose |
|---|---|
| `source_url` | Provenance and refresh |
| `publisher` | Attribution |
| `acquisition_timestamp` | When we fetched it |
| `effective_date` | When the source became effective |
| `jurisdiction` | Geographic scope |
| `geometry_crs_srid` | Coordinate reference system (SRID 4326 for storage, 2952 for Toronto computation) |
| `parser_version` | Reproducibility |
| `extraction_confidence` | Trust scoring |
| `license_status` | Legal compliance |
| `lineage_chain` | Full trace back to original file |

### Licensed Data Warnings

Some of the most valuable financial and comparable data is not fully open:

- **MLS / TRREB data**: Sale and lease comps require strict licensing review. TRREB restricts storage, redistribution, and derived exports.
- **MPAC assessment data**: Property assessment values; redistribution and bulk access restricted.
- **CoStar / Altus**: Commercial comps and construction costs; requires subscription agreement.
- **Private rent/sales feeds**: May limit how derived values appear in exports.

We must assume these require explicit licensing review before ingestion, storage, or export. The system must track `license_status` per source and enforce export restrictions at the report-generation layer.

---

## 8. Data Governance

### External Data Policy Requirements

- Track license status for every dataset and document.
- Track whether redistribution is allowed.
- Track whether exports may include derived values from licensed data.
- Retain source attribution in every user-facing result.
- MLS and proprietary market data likely require strict downstream-use rules.
- Retain retention and redistribution rules for uploaded planning documents.

### Internal Governance Requirements

- Freeze source versions used in every analysis.
- Never let LLM output become policy truth without validation.
- Route low-confidence extractions into review workflows.
- Support rollback of bad policy refreshes.
- Log all manual policy overrides.
- Deterministic rule evaluation must remain the source of truth.
- Every simulation must be reproducible against a frozen snapshot of inputs and data versions.
- Policy refreshes need audit logs and rollback capability.

### Security and Privacy Requirements

- Organization-scoped RBAC with SSO support.
- Row-level tenant isolation (all queries filtered by `organization_id`).
- Encryption at rest (AES-256) and in transit (TLS 1.3).
- Signed URLs for private document access with TTL expiry.
- Audit logs for exports and shared reports.
- Managed secret storage (AWS Secrets Manager / Railway variables).
- API key rotation support.
- Rate limiting per organization and per user.

---

## 9. AI Usage Policy

### Good Uses of AI

- Extracting clauses from messy/unstructured PDFs and bylaws
- Summarizing planning rationales and staff reports
- Semantic search over policies and precedents (natural language queries)
- Ranking likely precedent cases by similarity
- Generating draft summaries for analysts
- Generating candidate massing templates from typology descriptions
- Identifying cross-references between policy documents

### Bad Uses of AI

- Final legal compliance determination
- Final geometric calculations
- Final financial calculations
- Replacing citation chains with generated text
- Autonomous policy override decisions

### Operating Rule

LLMs may assist the system, but deterministic engines and versioned source data must remain authoritative. Every LLM-generated output must be tagged with `layer: "model_prediction"` and include the model version, prompt hash, and confidence score. No LLM output may be promoted to `layer: "source_fact"` or `layer: "derived_interpretation"` without human review or deterministic validation.

---

## 10. Policy Processing Pipeline

### Full Pipeline

```text
Raw Source File (PDF / HTML / GIS / CSV)
  -> Immutable raw storage (S3, keyed by SHA-256 hash)
  -> Parsing and OCR (PyMuPDF for PDF text, Tesseract fallback for scanned pages)
  -> Section and clause segmentation (regex + heading detection)
  -> LLM-assisted extraction (Claude API: clause -> canonical rule JSON)
  -> Canonical normalization (validate against rule JSON schema)
  -> Validation and confidence scoring (0.0–1.0 per extracted rule)
  -> Human review for low-confidence outputs (confidence < 0.85 -> review queue)
  -> Versioned policy graph (immutable policy_version snapshot)
  -> Online policy resolution (query: parcel -> applicable rules with citations)
```

### Canonical Rule Types for MVP

- Permitted uses
- Maximum height / minimum height
- FAR / FSI
- Lot coverage
- Front, rear, and side setbacks (by edge type)
- Stepbacks (by floor range)
- Angular plane or transition rules
- Lot frontage minima
- Lot area minima
- Parking ratios
- Loading requirements
- Amenity space requirements
- Open space / landscaping requirements
- Tower separation or distance constraints
- Density / unit count caps

### Policy Graph Requirements

Each clause must be able to point to:

- Source document page/section
- References to other clauses
- Applicability conditions (geometry filter, use filter)
- Jurisdiction and geography
- Effective date range
- Confidence of extraction
- Normalized output fields
- Parser version that produced the extraction

### Policy Override Hierarchy

Evaluation order (highest precedence first):

1. Site-specific exceptions (e.g., Section 37 agreements, site-specific bylaws)
2. Overlay zones (heritage, holding, floodplain)
3. Area-specific plans and secondary plans
4. Base zoning (By-law 569-2013 zone standards)
5. Official plan land use designations and general policies
6. Provincial policy statements and guidelines

### Zoning Rule JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ZoningRule",
  "type": "object",
  "required": ["rule_id", "rule_type", "jurisdiction_id", "source_clause_id", "effective_date", "confidence"],
  "properties": {
    "rule_id": {
      "type": "string",
      "format": "uuid"
    },
    "rule_type": {
      "type": "string",
      "enum": [
        "permitted_use", "max_height", "min_height", "far_fsi",
        "lot_coverage", "setback_front", "setback_rear", "setback_side",
        "stepback", "angular_plane", "lot_frontage_min", "lot_area_min",
        "parking_ratio", "loading", "amenity_space", "open_space",
        "tower_separation", "density_cap", "unit_count_cap"
      ]
    },
    "value": {
      "type": "number",
      "description": "Numeric value of the rule (metres, ratio, count, etc.)"
    },
    "value_unit": {
      "type": "string",
      "enum": ["m", "m2", "ratio", "pct", "units", "spaces", "spaces_per_unit"]
    },
    "value_min": {
      "type": ["number", "null"],
      "description": "Minimum bound if rule specifies a range"
    },
    "value_max": {
      "type": ["number", "null"],
      "description": "Maximum bound if rule specifies a range"
    },
    "condition": {
      "type": ["object", "null"],
      "description": "Applicability condition (use type, lot dimension, zone subclass)",
      "properties": {
        "use_type": { "type": ["string", "null"] },
        "zone_subclass": { "type": ["string", "null"] },
        "lot_frontage_min": { "type": ["number", "null"] },
        "lot_area_min": { "type": ["number", "null"] },
        "floor_range": {
          "type": ["object", "null"],
          "properties": {
            "from_floor": { "type": "integer" },
            "to_floor": { "type": ["integer", "null"] }
          }
        },
        "edge_type": {
          "type": ["string", "null"],
          "enum": [null, "front", "rear", "side_interior", "side_exterior", "flankage"]
        }
      }
    },
    "jurisdiction_id": { "type": "string", "format": "uuid" },
    "source_clause_id": { "type": "string", "format": "uuid" },
    "source_section_ref": { "type": "string" },
    "source_page_ref": { "type": ["string", "null"] },
    "effective_date": { "type": "string", "format": "date" },
    "expiry_date": { "type": ["string", "null"], "format": "date" },
    "confidence": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "parser_version": { "type": "string" },
    "override_level": {
      "type": "integer",
      "description": "Precedence: 1=site-specific, 2=overlay, 3=area-plan, 4=base-zoning, 5=official-plan, 6=provincial",
      "minimum": 1,
      "maximum": 6
    },
    "raw_text": {
      "type": "string",
      "description": "Original legislative text from which this rule was extracted"
    }
  }
}
```

### Example: Extracted Zoning Rule

```json
{
  "rule_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "rule_type": "max_height",
  "value": 36.0,
  "value_unit": "m",
  "value_min": null,
  "value_max": 36.0,
  "condition": {
    "use_type": "residential",
    "zone_subclass": "CR 3.0",
    "lot_frontage_min": null,
    "lot_area_min": null,
    "floor_range": null,
    "edge_type": null
  },
  "jurisdiction_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "source_clause_id": "clause-4928-uuid",
  "source_section_ref": "Section 40.10.40.10",
  "source_page_ref": null,
  "effective_date": "2013-05-09",
  "expiry_date": null,
  "confidence": 0.97,
  "parser_version": "1.2.0",
  "override_level": 4,
  "raw_text": "The height of a building or structure on a lot in a CR zone must not exceed 36.0 metres."
}
```

---

## 11. Technical Architecture

### Architecture Diagram

```text
                        +-------------------+
                        |   API Gateway     |
                        | (FastAPI + Auth)  |
                        | Rate limits,      |
                        | idempotency keys  |
                        +--------+----------+
                                 |
            +--------------------+--------------------+
            |                    |                    |
   +--------v-------+  +--------v-------+  +--------v--------+
   | Project Service|  | Geospatial Svc |  | Policy Service  |
   | (orgs, users,  |  | (parcel lookup,|  | (resolution,    |
   |  projects,     |  |  spatial joins, |  |  citations,     |
   |  scenarios)    |  |  overlay query) |  |  clause graph)  |
   +-------+--------+  +-------+--------+  +--------+--------+
           |                    |                    |
           +--------------------+--------------------+
                                |
            +-------------------+-------------------+
            |                   |                   |
   +--------v--------+ +-------v--------+ +--------v--------+
   | Simulation Svc  | | Finance Svc    | | Precedent Svc   |
   | (envelope,      | | (comps, costs, | | (retrieval,     |
   |  massing,       | |  pro forma,    | |  similarity,    |
   |  layout)        | |  valuation)    | |  scoring)       |
   +---------+-------+ +-------+--------+ +--------+--------+
             |                  |                   |
             +------------------+-------------------+
                                |
                    +-----------v-----------+
                    |    Export Service      |
                    | (PDF, CSV, XLSX, 3D)  |
                    +-----------+-----------+
                                |
   +----------------------------+----------------------------+
   |                            |                            |
   v                            v                            v
+--+------------+    +----------+--------+    +--------------+--+
| PostgreSQL    |    | S3 / MinIO        |    | Redis           |
| + PostGIS     |    | (raw docs,        |    | (cache, locks,  |
| + pgvector    |    |  artifacts,       |    |  job coord)     |
|               |    |  exports)         |    |                 |
+--+------------+    +-------------------+    +-----------------+
   |
   v
+--+------------+    +-------------------+
| OpenSearch    |    | Celery Workers    |
| (full-text,   |    | (OCR, parsing,    |
|  clause       |    |  massing, layout, |
|  search)      |    |  finance, export) |
+---------------+    +-------------------+
                            |
                     +------v------+
                     | Ingestion   |
                     | Orchestrator|
                     | (scheduled  |
                     |  refresh,   |
                     |  validation)|
                     +-------------+
```

### Core Service Map

| Service | Purpose | Key Libraries |
|---|---|---|
| API Gateway / Edge | Auth (JWT), rate limits, idempotency, routing | FastAPI, python-jose, slowapi |
| Project Service | Organizations, users, projects, shares, templates | SQLAlchemy, Pydantic |
| Geospatial Service | Parcel resolution, spatial joins, geometry metrics | GeoAlchemy2, Shapely, pyproj |
| Policy Service | Policy resolution, citations, clause graph, normalized rules | PyMuPDF, Claude API, Pydantic |
| Document Service | Raw document storage, OCR text, extraction artifacts | PyMuPDF, Tesseract (fallback), boto3 |
| Simulation Service | Envelope generation, massing runs, scenario diffing | Shapely, Trimesh, NumPy |
| Layout Service | Unit mix and floor-plate scenarios | OR-Tools (LP solver), NumPy, SciPy |
| Finance Service | Comparable normalization and financial outputs | NumPy, Pandas |
| Precedent Service | Retrieval, similarity, explainable risk scoring | pgvector, sentence-transformers, scikit-learn |
| Export Service | PDFs, CSVs, spreadsheets, 3D exports | WeasyPrint, openpyxl, Trimesh |
| Ingestion Orchestrator | Source refresh, parsing, validation, publish snapshots | Celery Beat, httpx, boto3 |

### Storage Architecture

| Store | Technology | Purpose |
|---|---|---|
| Primary RDBMS | PostgreSQL 16 + PostGIS 3.4 | Transactional data, spatial queries, parcel geometry |
| Vector Search | pgvector (MVP) | Semantic search over policy clauses, rationales, precedents |
| Object Storage | S3 / MinIO | Raw documents, OCR artifacts, generated reports, 3D exports |
| Cache / Locks | Redis 7 | Caching, distributed locks, Celery broker, short-lived coordination |
| Full-Text Search | OpenSearch 2.x | Full-text clause search, document retrieval, faceted filtering |

### Vector Search Details

- **Embedding model**: `all-MiniLM-L6-v2` (384 dimensions) for MVP; upgrade to domain-fine-tuned model later
- **Storage**: pgvector `vector(384)` column on `policy_clauses`, `rationale_extracts`, `application_documents`
- **Index**: IVFFlat with 100 lists for MVP (< 1M vectors); migrate to HNSW at scale
- **Query**: Cosine similarity with `<=>` operator; combine with structured filters for hybrid search

### Workflow and Scheduling

| Concern | MVP Tool | Growth Path |
|---|---|---|
| Async background jobs | Celery + Redis broker | Temporal for workflow-heavy operations |
| Scheduled ingestion | Celery Beat | Dagster or Airflow for DAG-based pipelines |
| Long-running analysis | Celery task chains | Temporal workflows with retry and visibility |
| Job status tracking | Custom `job_status` table + polling | Temporal UI / Dagster UI |

---

## 12. Database Schema

```sql
-- =============================================================================
-- EXTENSIONS
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";
CREATE EXTENSION IF NOT EXISTS "vector";

-- =============================================================================
-- 1. TENANT AND PROJECT MODEL
-- =============================================================================

CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    settings_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_organizations_slug ON organizations (slug);

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    password_hash   TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_users_email ON users (email);

CREATE TABLE workspace_members (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'analyst', 'viewer')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, user_id)
);
CREATE INDEX idx_workspace_members_org ON workspace_members (organization_id);
CREATE INDEX idx_workspace_members_user ON workspace_members (user_id);

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by      UUID NOT NULL REFERENCES users(id),
    name            TEXT NOT NULL,
    description     TEXT,
    status          TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_projects_org ON projects (organization_id);
CREATE INDEX idx_projects_status ON projects (organization_id, status);

CREATE TABLE project_shares (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    shared_with     UUID NOT NULL REFERENCES users(id),
    permission      TEXT NOT NULL CHECK (permission IN ('view', 'edit', 'admin')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, shared_with)
);

CREATE TABLE scenario_runs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id          UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parent_scenario_id  UUID REFERENCES scenario_runs(id),
    scenario_type       TEXT NOT NULL CHECK (scenario_type IN ('base', 'variance', 'optimization')),
    label               TEXT,
    input_hash          TEXT NOT NULL,
    source_snapshot_id  UUID,
    status              TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);
CREATE INDEX idx_scenario_runs_project ON scenario_runs (project_id);
CREATE INDEX idx_scenario_runs_parent ON scenario_runs (parent_scenario_id);
CREATE INDEX idx_scenario_runs_input_hash ON scenario_runs (input_hash);

-- =============================================================================
-- 2. JURISDICTIONS AND PARCELS
-- =============================================================================

CREATE TABLE jurisdictions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    province        TEXT NOT NULL,
    country         TEXT NOT NULL DEFAULT 'CA',
    bbox_geom       geometry(Polygon, 4326),
    timezone        TEXT NOT NULL DEFAULT 'America/Toronto',
    metadata_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_jurisdictions_bbox ON jurisdictions USING GIST (bbox_geom);

CREATE TABLE parcels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    pin             TEXT,
    address         TEXT,
    geom            geometry(MultiPolygon, 4326) NOT NULL,
    geom_area_m2    DOUBLE PRECISION GENERATED ALWAYS AS (ST_Area(geom::geography)) STORED,
    lot_area_m2     DOUBLE PRECISION,
    lot_frontage_m  DOUBLE PRECISION,
    lot_depth_m     DOUBLE PRECISION,
    current_use     TEXT,
    assessed_value  NUMERIC(14,2),
    zone_code       TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction_id, pin)
);
CREATE INDEX idx_parcels_geom ON parcels USING GIST (geom);
CREATE INDEX idx_parcels_jurisdiction ON parcels (jurisdiction_id);
CREATE INDEX idx_parcels_zone ON parcels (jurisdiction_id, zone_code);
CREATE INDEX idx_parcels_address ON parcels USING GIN (to_tsvector('english', coalesce(address, '')));

CREATE TABLE parcel_metrics (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parcel_id       UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    metric_type     TEXT NOT NULL,
    metric_value    DOUBLE PRECISION NOT NULL,
    unit            TEXT NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (parcel_id, metric_type)
);
CREATE INDEX idx_parcel_metrics_parcel ON parcel_metrics (parcel_id);

CREATE TABLE project_parcels (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    parcel_id       UUID NOT NULL REFERENCES parcels(id),
    role            TEXT NOT NULL DEFAULT 'primary' CHECK (role IN ('primary', 'assembly', 'context')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, parcel_id)
);

-- =============================================================================
-- 3. POLICY MODEL
-- =============================================================================

CREATE TABLE policy_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    doc_type        TEXT NOT NULL CHECK (doc_type IN (
                        'zoning_bylaw', 'official_plan', 'secondary_plan',
                        'design_guideline', 'amendment', 'site_specific',
                        'overlay', 'provincial_policy'
                    )),
    title           TEXT NOT NULL,
    source_url      TEXT,
    effective_date  DATE,
    expiry_date     DATE,
    object_key      TEXT NOT NULL,
    file_hash       TEXT NOT NULL,
    parse_status    TEXT NOT NULL DEFAULT 'pending' CHECK (parse_status IN ('pending', 'parsing', 'parsed', 'failed', 'reviewed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_policy_docs_jurisdiction ON policy_documents (jurisdiction_id);
CREATE INDEX idx_policy_docs_type ON policy_documents (jurisdiction_id, doc_type);
CREATE INDEX idx_policy_docs_hash ON policy_documents (file_hash);

CREATE TABLE policy_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES policy_documents(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    parser_version  TEXT NOT NULL,
    extracted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    confidence_avg  DOUBLE PRECISION,
    confidence_min  DOUBLE PRECISION,
    clause_count    INTEGER NOT NULL DEFAULT 0,
    published_at    TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (document_id, version_number)
);
CREATE INDEX idx_policy_versions_active ON policy_versions (document_id) WHERE is_active = true;

CREATE TABLE policy_clauses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_version_id   UUID NOT NULL REFERENCES policy_versions(id) ON DELETE CASCADE,
    section_ref         TEXT NOT NULL,
    page_ref            TEXT,
    raw_text            TEXT NOT NULL,
    normalized_type     TEXT NOT NULL,
    normalized_json     JSONB NOT NULL,
    confidence          DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    needs_review        BOOLEAN NOT NULL DEFAULT false,
    reviewed_at         TIMESTAMPTZ,
    reviewed_by         UUID REFERENCES users(id),
    embedding           vector(384),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_policy_clauses_version ON policy_clauses (policy_version_id);
CREATE INDEX idx_policy_clauses_type ON policy_clauses (normalized_type);
CREATE INDEX idx_policy_clauses_review ON policy_clauses (needs_review) WHERE needs_review = true;
CREATE INDEX idx_policy_clauses_embedding ON policy_clauses USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_policy_clauses_text ON policy_clauses USING GIN (to_tsvector('english', raw_text));

CREATE TABLE policy_references (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_clause_id  UUID NOT NULL REFERENCES policy_clauses(id) ON DELETE CASCADE,
    to_clause_id    UUID NOT NULL REFERENCES policy_clauses(id) ON DELETE CASCADE,
    relation_type   TEXT NOT NULL CHECK (relation_type IN ('amends', 'overrides', 'references', 'defines', 'exempts')),
    UNIQUE (from_clause_id, to_clause_id, relation_type)
);
CREATE INDEX idx_policy_refs_from ON policy_references (from_clause_id);
CREATE INDEX idx_policy_refs_to ON policy_references (to_clause_id);

CREATE TABLE policy_applicability_rules (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_clause_id    UUID NOT NULL REFERENCES policy_clauses(id) ON DELETE CASCADE,
    jurisdiction_id     UUID NOT NULL REFERENCES jurisdictions(id),
    geometry_filter     geometry(MultiPolygon, 4326),
    zone_filter         TEXT[],
    use_filter          TEXT[],
    override_level      INTEGER NOT NULL CHECK (override_level BETWEEN 1 AND 6),
    applicability_json  JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_applicability_clause ON policy_applicability_rules (policy_clause_id);
CREATE INDEX idx_applicability_geom ON policy_applicability_rules USING GIST (geometry_filter);
CREATE INDEX idx_applicability_zone ON policy_applicability_rules USING GIN (zone_filter);

-- =============================================================================
-- 4. DATASET LAYERS
-- =============================================================================

CREATE TABLE dataset_layers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    name            TEXT NOT NULL,
    layer_type      TEXT NOT NULL CHECK (layer_type IN (
                        'transit', 'heritage', 'floodplain', 'environmental',
                        'road', 'amenity', 'demographic', 'building_mass', 'other'
                    )),
    source_url      TEXT,
    license_status  TEXT NOT NULL DEFAULT 'unknown' CHECK (license_status IN ('open', 'restricted', 'licensed', 'unknown')),
    refresh_frequency TEXT,
    last_refreshed  TIMESTAMPTZ,
    published_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction_id, name)
);

CREATE TABLE dataset_features (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_layer_id    UUID NOT NULL REFERENCES dataset_layers(id) ON DELETE CASCADE,
    source_record_id    TEXT,
    geom                geometry(Geometry, 4326) NOT NULL,
    attributes_json     JSONB NOT NULL DEFAULT '{}',
    effective_date      DATE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_dataset_features_layer ON dataset_features (dataset_layer_id);
CREATE INDEX idx_dataset_features_geom ON dataset_features USING GIST (geom);

CREATE TABLE feature_to_parcel_links (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_id          UUID NOT NULL REFERENCES dataset_features(id) ON DELETE CASCADE,
    parcel_id           UUID NOT NULL REFERENCES parcels(id) ON DELETE CASCADE,
    relationship_type   TEXT NOT NULL DEFAULT 'intersects' CHECK (relationship_type IN ('intersects', 'contains', 'within', 'adjacent')),
    UNIQUE (feature_id, parcel_id, relationship_type)
);
CREATE INDEX idx_feature_parcel_feature ON feature_to_parcel_links (feature_id);
CREATE INDEX idx_feature_parcel_parcel ON feature_to_parcel_links (parcel_id);

-- =============================================================================
-- 5. DEVELOPMENT APPLICATIONS AND PRECEDENTS
-- =============================================================================

CREATE TABLE development_applications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    app_number      TEXT NOT NULL,
    address         TEXT,
    parcel_id       UUID REFERENCES parcels(id),
    geom            geometry(Point, 4326),
    app_type        TEXT NOT NULL,
    status          TEXT NOT NULL,
    decision        TEXT CHECK (decision IN ('approved', 'refused', 'withdrawn', 'pending', 'appealed')),
    decision_date   DATE,
    proposed_height_m   DOUBLE PRECISION,
    proposed_units      INTEGER,
    proposed_fsi        DOUBLE PRECISION,
    proposed_use        TEXT,
    metadata_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (jurisdiction_id, app_number)
);
CREATE INDEX idx_dev_apps_jurisdiction ON development_applications (jurisdiction_id);
CREATE INDEX idx_dev_apps_geom ON development_applications USING GIST (geom);
CREATE INDEX idx_dev_apps_parcel ON development_applications (parcel_id);
CREATE INDEX idx_dev_apps_decision ON development_applications (decision);
CREATE INDEX idx_dev_apps_type ON development_applications (app_type);

CREATE TABLE application_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id  UUID NOT NULL REFERENCES development_applications(id) ON DELETE CASCADE,
    doc_type        TEXT NOT NULL CHECK (doc_type IN ('staff_report', 'planning_rationale', 'drawings', 'data_sheet', 'decision_letter', 'other')),
    object_key      TEXT NOT NULL,
    extracted_text  TEXT,
    embedding       vector(384),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_app_docs_application ON application_documents (application_id);
CREATE INDEX idx_app_docs_embedding ON application_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

CREATE TABLE rationale_extracts (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_document_id UUID NOT NULL REFERENCES application_documents(id) ON DELETE CASCADE,
    extract_type            TEXT NOT NULL CHECK (extract_type IN ('planning_rationale', 'staff_recommendation', 'condition', 'policy_reference', 'design_comment')),
    content                 TEXT NOT NULL,
    confidence              DOUBLE PRECISION NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    embedding               vector(384),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_rationale_doc ON rationale_extracts (application_document_id);
CREATE INDEX idx_rationale_embedding ON rationale_extracts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- =============================================================================
-- 6. SIMULATION, MASSING, AND LAYOUT
-- =============================================================================

CREATE TABLE massing_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL UNIQUE,
    typology        TEXT NOT NULL CHECK (typology IN ('tower', 'midrise', 'lowrise', 'townhouse', 'mixed', 'custom')),
    parameters_json JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE massings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_run_id     UUID NOT NULL REFERENCES scenario_runs(id) ON DELETE CASCADE,
    template_id         UUID REFERENCES massing_templates(id),
    template_name       TEXT,
    geometry_3d_key     TEXT,
    envelope_2d         geometry(Polygon, 4326),
    total_gfa_m2        DOUBLE PRECISION,
    total_gla_m2        DOUBLE PRECISION,
    storeys             INTEGER,
    height_m            DOUBLE PRECISION,
    lot_coverage_pct    DOUBLE PRECISION,
    fsi                 DOUBLE PRECISION,
    summary_json        JSONB NOT NULL DEFAULT '{}',
    compliance_json     JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_massings_scenario ON massings (scenario_run_id);

CREATE TABLE unit_types (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID REFERENCES jurisdictions(id),
    name            TEXT NOT NULL,
    bedroom_count   INTEGER NOT NULL CHECK (bedroom_count >= 0),
    min_area_m2     DOUBLE PRECISION NOT NULL,
    max_area_m2     DOUBLE PRECISION NOT NULL,
    typical_area_m2 DOUBLE PRECISION NOT NULL,
    min_width_m     DOUBLE PRECISION,
    is_accessible   BOOLEAN NOT NULL DEFAULT false,
    CHECK (min_area_m2 <= typical_area_m2 AND typical_area_m2 <= max_area_m2)
);

CREATE TABLE layout_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    massing_id      UUID NOT NULL REFERENCES massings(id) ON DELETE CASCADE,
    objective       TEXT NOT NULL DEFAULT 'max_revenue' CHECK (objective IN ('max_revenue', 'max_units', 'balanced', 'custom')),
    constraints_json JSONB NOT NULL DEFAULT '{}',
    result_json     JSONB,
    total_units     INTEGER,
    total_area_m2   DOUBLE PRECISION,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_layout_runs_massing ON layout_runs (massing_id);

-- =============================================================================
-- 7. FINANCE
-- =============================================================================

CREATE TABLE market_comparables (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    comp_type       TEXT NOT NULL CHECK (comp_type IN ('rental', 'sale', 'land_sale', 'construction_cost')),
    address         TEXT,
    geom            geometry(Point, 4326),
    effective_date  DATE NOT NULL,
    source          TEXT NOT NULL,
    license_status  TEXT NOT NULL DEFAULT 'unknown',
    attributes_json JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_market_comps_jurisdiction ON market_comparables (jurisdiction_id);
CREATE INDEX idx_market_comps_type ON market_comparables (comp_type);
CREATE INDEX idx_market_comps_geom ON market_comparables USING GIST (geom);
CREATE INDEX idx_market_comps_date ON market_comparables (effective_date DESC);

CREATE TABLE financial_assumption_sets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id),
    name            TEXT NOT NULL,
    is_default      BOOLEAN NOT NULL DEFAULT false,
    assumptions_json JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE financial_runs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_run_id     UUID NOT NULL REFERENCES scenario_runs(id) ON DELETE CASCADE,
    assumption_set_id   UUID NOT NULL REFERENCES financial_assumption_sets(id),
    layout_run_id       UUID REFERENCES layout_runs(id),
    output_json         JSONB NOT NULL,
    total_revenue       NUMERIC(14,2),
    total_cost          NUMERIC(14,2),
    noi                 NUMERIC(14,2),
    valuation           NUMERIC(14,2),
    residual_land_value NUMERIC(14,2),
    irr_pct             DOUBLE PRECISION,
    status              TEXT NOT NULL DEFAULT 'completed',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_financial_runs_scenario ON financial_runs (scenario_run_id);

-- =============================================================================
-- 8. ENTITLEMENT AND PRECEDENT
-- =============================================================================

CREATE TABLE entitlement_results (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_run_id     UUID NOT NULL REFERENCES scenario_runs(id) ON DELETE CASCADE,
    source_snapshot_id  UUID,
    overall_compliance  TEXT NOT NULL CHECK (overall_compliance IN ('compliant', 'minor_variance', 'major_variance', 'non_compliant')),
    result_json         JSONB NOT NULL,
    score               DOUBLE PRECISION CHECK (score >= 0.0 AND score <= 1.0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_entitlement_results_scenario ON entitlement_results (scenario_run_id);

CREATE TABLE precedent_searches (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_run_id     UUID NOT NULL REFERENCES scenario_runs(id) ON DELETE CASCADE,
    search_params_json  JSONB NOT NULL,
    result_count        INTEGER NOT NULL DEFAULT 0,
    results_json        JSONB NOT NULL DEFAULT '[]',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_precedent_searches_scenario ON precedent_searches (scenario_run_id);

-- =============================================================================
-- 9. EXPORTS AND AUDIT
-- =============================================================================

CREATE TABLE export_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    scenario_run_id UUID REFERENCES scenario_runs(id),
    export_type     TEXT NOT NULL CHECK (export_type IN ('pdf', 'csv', 'xlsx', 'glb', 'obj', 'bundle')),
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'generating', 'completed', 'failed')),
    object_key      TEXT,
    signed_url      TEXT,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ
);
CREATE INDEX idx_export_jobs_project ON export_jobs (project_id);

CREATE TABLE audit_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    actor_id        UUID REFERENCES users(id),
    event_type      TEXT NOT NULL,
    entity_type     TEXT NOT NULL,
    entity_id       UUID,
    payload_json    JSONB NOT NULL DEFAULT '{}',
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_events_org ON audit_events (organization_id);
CREATE INDEX idx_audit_events_type ON audit_events (event_type);
CREATE INDEX idx_audit_events_entity ON audit_events (entity_type, entity_id);
CREATE INDEX idx_audit_events_created ON audit_events (created_at DESC);

-- =============================================================================
-- 10. INGESTION AND SOURCE MANAGEMENT
-- =============================================================================

CREATE TABLE source_snapshots (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    snapshot_type   TEXT NOT NULL,
    version_label   TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at    TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT false,
    UNIQUE (jurisdiction_id, snapshot_type, version_label)
);
CREATE INDEX idx_source_snapshots_active ON source_snapshots (jurisdiction_id, snapshot_type) WHERE is_active = true;

CREATE TABLE ingestion_jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jurisdiction_id UUID NOT NULL REFERENCES jurisdictions(id),
    source_url      TEXT NOT NULL,
    job_type        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'review_needed')),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    records_processed INTEGER DEFAULT 0,
    records_failed  INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs (status);
CREATE INDEX idx_ingestion_jobs_jurisdiction ON ingestion_jobs (jurisdiction_id);
```

---

## 13. Key Algorithms with Pseudocode

### Algorithm 1: Building Envelope Generation

10-step deterministic pipeline using Shapely (2D) and Trimesh (3D).

```python
def generate_envelope(parcel_geom, policy_rules, overlay_constraints):
    """
    Generate a buildable envelope from parcel geometry and policy constraints.
    All geometry in SRID 2952 (NAD83 / MTM zone 10, metres) for computation.
    Returns envelope geometry + compliance deltas for each rule.
    """
    # Step 1: Project to local CRS for metre-accurate computation
    parcel_local = transform_to_srid(parcel_geom, target_srid=2952)  # pyproj

    # Step 2: Classify parcel edges (front, rear, side, flankage)
    edges = classify_edges(parcel_local, road_network)
    # Uses nearest-road-segment matching + angle heuristics
    # front = edge closest to primary road; rear = opposite; sides = remainder

    # Step 3: Compute setback lines per edge type
    setback_lines = {}
    for edge in edges:
        rule = find_rule(policy_rules, rule_type=f"setback_{edge.type}")
        setback_lines[edge.id] = edge.geometry.parallel_offset(
            rule.value, side='right'  # Shapely parallel_offset
        )

    # Step 4: Compute buildable footprint by intersecting setback insets
    buildable = parcel_local
    for edge_id, setback_line in setback_lines.items():
        inset_polygon = create_inset_polygon(parcel_local, setback_line)
        buildable = buildable.intersection(inset_polygon)  # Shapely intersection

    # Step 5: Apply lot coverage constraint
    max_coverage = find_rule(policy_rules, rule_type="lot_coverage")
    max_footprint_area = parcel_local.area * max_coverage.value
    if buildable.area > max_footprint_area:
        buildable = shrink_to_area(buildable, max_footprint_area)

    # Step 6: Compute height regimes per floor
    max_height_rule = find_rule(policy_rules, rule_type="max_height")
    stepback_rules = find_rules(policy_rules, rule_type="stepback")
    floor_height = 3.0  # metres per storey (configurable)
    max_storeys = int(max_height_rule.value / floor_height)

    floor_plates = []
    current_footprint = buildable
    for floor_num in range(1, max_storeys + 1):
        # Apply stepback for this floor range
        for rule in stepback_rules:
            if rule.condition.floor_range.from_floor <= floor_num:
                if rule.condition.floor_range.to_floor is None or floor_num <= rule.condition.floor_range.to_floor:
                    current_footprint = current_footprint.buffer(
                        -rule.value  # negative buffer = inward stepback
                    )
        if current_footprint.area < 50:  # minimum viable floor plate
            break
        floor_plates.append({
            "floor": floor_num,
            "footprint": current_footprint,
            "area_m2": current_footprint.area
        })

    # Step 7: Apply angular plane constraints
    angular_rules = find_rules(policy_rules, rule_type="angular_plane")
    for rule in angular_rules:
        # Typically: 45-degree plane from property line at certain height
        # Clip floor plates that exceed the angular plane surface
        for plate in floor_plates:
            elevation = plate["floor"] * floor_height
            max_extent = compute_angular_limit(
                edge=rule.condition.edge_type,
                base_height=rule.condition.get("base_height", 10.5),
                angle_deg=rule.value,
                elevation=elevation,
                parcel=parcel_local
            )
            plate["footprint"] = plate["footprint"].intersection(max_extent)

    # Step 8: Compute GFA and check FAR/FSI constraint
    total_gfa = sum(p["area_m2"] for p in floor_plates)
    fsi_rule = find_rule(policy_rules, rule_type="far_fsi")
    max_gfa = parcel_local.area * fsi_rule.value
    if total_gfa > max_gfa:
        # Remove floors from top until compliant
        while total_gfa > max_gfa and floor_plates:
            removed = floor_plates.pop()
            total_gfa -= removed["area_m2"]

    # Step 9: Generate 3D envelope mesh
    envelope_3d = extrude_floor_plates(floor_plates, floor_height)  # Trimesh

    # Step 10: Compute compliance deltas for every rule
    compliance = []
    for rule in policy_rules:
        actual = compute_actual_value(rule.rule_type, floor_plates, parcel_local)
        compliance.append({
            "rule_type": rule.rule_type,
            "rule_value": rule.value,
            "actual_value": actual,
            "delta": actual - rule.value,
            "compliant": is_compliant(rule, actual),
            "source_clause_id": rule.source_clause_id,
            "confidence": rule.confidence
        })

    return {
        "floor_plates": floor_plates,
        "envelope_3d": envelope_3d,
        "total_gfa_m2": total_gfa,
        "storeys": len(floor_plates),
        "height_m": len(floor_plates) * floor_height,
        "lot_coverage_pct": floor_plates[0]["area_m2"] / parcel_local.area if floor_plates else 0,
        "fsi": total_gfa / parcel_local.area,
        "compliance": compliance,
        "input_hash": hash_inputs(parcel_geom, policy_rules, overlay_constraints)
    }
```

### Algorithm 2: Unit Mix Optimization

Full LP formulation using OR-Tools.

```python
from ortools.linear_solver import pywraplp

def optimize_unit_mix(
    usable_gla_m2: float,
    unit_types: list,       # [{name, bedroom_count, typical_area_m2, rent_per_m2, min_pct, max_pct}]
    policy_constraints: dict,
    floor_plates: list,
    objective: str = "max_revenue"
):
    """
    Linear programming formulation for unit mix optimization.
    Decision variables: count of each unit type.
    """
    solver = pywraplp.Solver.CreateSolver('GLOP')

    # --- Decision variables ---
    # x[i] = number of units of type i
    x = {}
    for i, ut in enumerate(unit_types):
        x[i] = solver.IntVar(0, 1000, f'x_{ut["name"]}')

    total_units = solver.Sum(x[i] for i in range(len(unit_types)))

    # --- Constraint 1: Total area <= usable GLA ---
    solver.Add(
        solver.Sum(x[i] * unit_types[i]["typical_area_m2"] for i in range(len(unit_types)))
        <= usable_gla_m2
    )

    # --- Constraint 2: Unit counts >= 0 (implicit in IntVar) ---

    # --- Constraint 3: Minimum unit mix ratios (policy or user) ---
    # e.g., at least 15% 2-bedroom, at least 10% 3-bedroom
    for i, ut in enumerate(unit_types):
        if ut.get("min_pct"):
            solver.Add(x[i] >= total_units * ut["min_pct"])
        if ut.get("max_pct"):
            solver.Add(x[i] <= total_units * ut["max_pct"])

    # --- Constraint 4: Parking requirements ---
    parking_ratio = policy_constraints.get("parking_ratio", 0.8)  # spaces per unit
    max_parking = policy_constraints.get("max_parking_spaces", 500)
    solver.Add(
        solver.Sum(x[i] * parking_ratio for i in range(len(unit_types)))
        <= max_parking
    )

    # --- Constraint 5: Accessibility requirements ---
    accessible_pct = policy_constraints.get("accessible_pct", 0.15)
    accessible_types = [i for i, ut in enumerate(unit_types) if ut.get("is_accessible")]
    if accessible_types:
        solver.Add(
            solver.Sum(x[i] for i in accessible_types)
            >= total_units * accessible_pct
        )

    # --- Constraint 6: Floor plate capacity ---
    # Total units per floor <= floor_plate_area / avg_unit_area
    avg_unit_area = sum(ut["typical_area_m2"] for ut in unit_types) / len(unit_types)
    max_units_per_floor = max(
        int(plate["area_m2"] / avg_unit_area) for plate in floor_plates
    )
    num_floors = len(floor_plates)
    solver.Add(total_units <= max_units_per_floor * num_floors)

    # --- Constraint 7: Maximum density (units/hectare) from policy ---
    if policy_constraints.get("max_density_uph"):
        site_area_ha = policy_constraints["site_area_m2"] / 10000
        solver.Add(total_units <= policy_constraints["max_density_uph"] * site_area_ha)

    # --- Constraint 8: Amenity space ---
    amenity_per_unit_m2 = policy_constraints.get("amenity_per_unit_m2", 2.0)
    total_amenity_required = solver.Sum(x[i] * amenity_per_unit_m2 for i in range(len(unit_types)))
    amenity_available_m2 = policy_constraints.get("amenity_available_m2", usable_gla_m2 * 0.05)
    solver.Add(total_amenity_required <= amenity_available_m2)

    # --- Objective function ---
    if objective == "max_revenue":
        # Maximize annual gross revenue
        solver.Maximize(
            solver.Sum(
                x[i] * unit_types[i]["typical_area_m2"] * unit_types[i]["rent_per_m2"] * 12
                for i in range(len(unit_types))
            )
        )
    elif objective == "max_units":
        solver.Maximize(total_units)
    elif objective == "balanced":
        # Weighted: 70% revenue + 30% unit count
        max_possible_revenue = usable_gla_m2 * max(ut["rent_per_m2"] for ut in unit_types) * 12
        solver.Maximize(
            0.7 * solver.Sum(
                x[i] * unit_types[i]["typical_area_m2"] * unit_types[i]["rent_per_m2"] * 12
                for i in range(len(unit_types))
            ) / max_possible_revenue
            + 0.3 * total_units / 500  # normalized
        )

    # --- Solve ---
    status = solver.Solve()
    if status != pywraplp.Solver.OPTIMAL:
        return {"status": "infeasible", "units": []}

    result_units = []
    for i, ut in enumerate(unit_types):
        count = int(x[i].solution_value())
        if count > 0:
            result_units.append({
                "unit_type": ut["name"],
                "bedroom_count": ut["bedroom_count"],
                "count": count,
                "area_each_m2": ut["typical_area_m2"],
                "total_area_m2": count * ut["typical_area_m2"],
                "annual_revenue": count * ut["typical_area_m2"] * ut["rent_per_m2"] * 12
            })

    return {
        "status": "optimal",
        "units": result_units,
        "total_units": sum(u["count"] for u in result_units),
        "total_area_m2": sum(u["total_area_m2"] for u in result_units),
        "total_annual_revenue": sum(u["annual_revenue"] for u in result_units),
        "utilization_pct": sum(u["total_area_m2"] for u in result_units) / usable_gla_m2 * 100
    }
```

### Algorithm 3: Entitlement Scoring

Two-layer system: retrieval + explainable scoring.

```python
import numpy as np
from sentence_transformers import SentenceTransformer

# --- Layer 1: Retrieval ---

def retrieve_precedents(project, parcel, db, top_k=20):
    """
    Find nearby and structurally similar precedent applications.
    Combines spatial proximity, form similarity, and textual similarity.
    """
    # Spatial: applications within 500m radius
    spatial_candidates = db.execute("""
        SELECT da.*, ST_Distance(da.geom::geography, :parcel_geom::geography) as distance_m
        FROM development_applications da
        WHERE ST_DWithin(da.geom::geography, :parcel_geom::geography, 500)
          AND da.decision IS NOT NULL
          AND da.decision_date > now() - interval '7 years'
        ORDER BY distance_m ASC
        LIMIT 50
    """, {"parcel_geom": parcel.geom})

    # Form similarity: compare proposed height, FSI, use
    form_scores = []
    for candidate in spatial_candidates:
        height_sim = 1.0 - min(abs(project.height_m - (candidate.proposed_height_m or 0)) / 50.0, 1.0)
        fsi_sim = 1.0 - min(abs(project.fsi - (candidate.proposed_fsi or 0)) / 5.0, 1.0)
        use_match = 1.0 if project.use == candidate.proposed_use else 0.3
        form_score = 0.4 * height_sim + 0.4 * fsi_sim + 0.2 * use_match
        form_scores.append((candidate, form_score))

    # Textual similarity: embed project description vs. rationale extracts
    model = SentenceTransformer('all-MiniLM-L6-v2')
    project_embedding = model.encode(project.description)
    for candidate, form_score in form_scores:
        # Use pgvector for fast cosine similarity against rationale embeddings
        text_sim = db.execute("""
            SELECT MAX(1 - (re.embedding <=> :query_embedding)) as similarity
            FROM rationale_extracts re
            JOIN application_documents ad ON re.application_document_id = ad.id
            WHERE ad.application_id = :app_id
        """, {"query_embedding": project_embedding, "app_id": candidate.id})
        candidate.text_similarity = text_sim or 0.0

    # Combine scores: 30% spatial, 40% form, 30% text
    ranked = []
    for candidate, form_score in form_scores:
        spatial_score = 1.0 - min(candidate.distance_m / 500.0, 1.0)
        combined = 0.3 * spatial_score + 0.4 * form_score + 0.3 * candidate.text_similarity
        ranked.append((candidate, combined))

    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked[:top_k]


# --- Layer 2: Explainable Scoring ---

def score_entitlement(project, policy_rules, precedents):
    """
    Produce an approval-likelihood score using explainable features.
    Each feature contributes a weighted component to the final score.
    """
    features = {}

    # Feature 1: Compliance delta (0-1, higher = more compliant)
    violations = []
    for rule in policy_rules:
        actual = project.get_metric(rule.rule_type)
        if actual is not None and not is_compliant(rule, actual):
            delta_pct = abs(actual - rule.value) / max(rule.value, 1)
            violations.append(delta_pct)
    features["compliance_score"] = max(0, 1.0 - sum(violations) / max(len(policy_rules), 1))

    # Feature 2: Variance magnitude (0-1, lower variance = higher score)
    if violations:
        avg_violation = np.mean(violations)
        features["variance_magnitude"] = max(0, 1.0 - avg_violation)
    else:
        features["variance_magnitude"] = 1.0

    # Feature 3: Precedent density (0-1)
    approved_nearby = sum(1 for p, _ in precedents if p.decision == 'approved')
    total_nearby = len(precedents)
    features["precedent_density"] = min(approved_nearby / 5.0, 1.0)  # 5+ approved = max score

    # Feature 4: Precedent approval rate (0-1)
    if total_nearby > 0:
        features["precedent_approval_rate"] = approved_nearby / total_nearby
    else:
        features["precedent_approval_rate"] = 0.5  # no data = neutral

    # Feature 5: District similarity (0-1)
    # Average form similarity of top-5 precedents
    top5_sims = [score for _, score in precedents[:5]]
    features["district_similarity"] = np.mean(top5_sims) if top5_sims else 0.0

    # Feature 6: Rationale similarity (0-1)
    top5_text_sims = [p.text_similarity for p, _ in precedents[:5] if hasattr(p, 'text_similarity')]
    features["rationale_similarity"] = np.mean(top5_text_sims) if top5_text_sims else 0.0

    # Weighted combination
    weights = {
        "compliance_score": 0.30,
        "variance_magnitude": 0.15,
        "precedent_density": 0.15,
        "precedent_approval_rate": 0.20,
        "district_similarity": 0.10,
        "rationale_similarity": 0.10
    }

    final_score = sum(features[k] * weights[k] for k in weights)

    return {
        "approval_likelihood": round(final_score, 3),
        "features": {k: round(v, 3) for k, v in features.items()},
        "weights": weights,
        "precedent_count": total_nearby,
        "approved_count": approved_nearby,
        "explainability_layer": "model_prediction",
        "model_version": "entitlement-v1.0"
    }
```

### Algorithm 4: Pro Forma Calculation

11-step financial model with formulas and value tagging.

```python
def calculate_pro_forma(
    unit_mix: list,          # from layout optimizer
    assumptions: dict,       # from financial_assumption_set
    market_comps: list,      # from market_comparables
    parcel_area_m2: float,
    total_gfa_m2: float,
):
    """
    11-step pro forma calculation.
    Each output is tagged with its explainability layer.
    """
    results = {}
    tags = {}  # value_tag -> explainability layer

    # Step 1: Resolve rent/sale comps per unit type
    # Use distance-weighted average of comparables within 1km, < 2 years old
    unit_revenues = {}
    for unit in unit_mix:
        matching_comps = [c for c in market_comps
                         if c["comp_type"] == assumptions.get("tenure", "rental")
                         and c["attributes_json"].get("bedroom_count") == unit["bedroom_count"]]
        if matching_comps:
            avg_rate = np.mean([c["attributes_json"]["rate_per_m2"] for c in matching_comps])
            tags[f"rent_{unit['unit_type']}"] = "source_fact"
        else:
            avg_rate = assumptions.get(f"default_rent_{unit['bedroom_count']}br", 25.0)
            tags[f"rent_{unit['unit_type']}"] = "simulation_assumption"
        unit_revenues[unit["unit_type"]] = avg_rate
    results["unit_revenues_per_m2"] = unit_revenues

    # Step 2: Calculate gross potential revenue
    if assumptions.get("tenure") == "rental":
        # Annual rental revenue
        gross_revenue = sum(
            unit["count"] * unit["area_each_m2"] * unit_revenues[unit["unit_type"]] * 12
            for unit in unit_mix
        )
        tags["gross_revenue"] = "derived_interpretation"
    else:
        # Sale revenue
        gross_revenue = sum(
            unit["count"] * unit["area_each_m2"] * unit_revenues[unit["unit_type"]]
            for unit in unit_mix
        )
        tags["gross_revenue"] = "derived_interpretation"
    results["gross_potential_revenue"] = round(gross_revenue, 2)

    # Step 3: Apply vacancy and collection loss
    vacancy_rate = assumptions.get("vacancy_rate", 0.03)
    tags["vacancy_rate"] = "simulation_assumption"
    effective_gross_income = gross_revenue * (1 - vacancy_rate)
    results["effective_gross_income"] = round(effective_gross_income, 2)

    # Step 4: Calculate operating expenses
    opex_per_unit = assumptions.get("opex_per_unit_annual", 5000)
    tags["opex_per_unit"] = "simulation_assumption"
    total_units = sum(u["count"] for u in unit_mix)
    total_opex = opex_per_unit * total_units
    results["total_operating_expenses"] = round(total_opex, 2)

    # Step 5: Calculate NOI (Net Operating Income)
    # NOI = Effective Gross Income - Operating Expenses
    noi = effective_gross_income - total_opex
    results["noi"] = round(noi, 2)
    tags["noi"] = "derived_interpretation"

    # Step 6: Estimate stabilized value
    # Value = NOI / Cap Rate
    cap_rate = assumptions.get("cap_rate", 0.045)
    tags["cap_rate"] = "simulation_assumption"
    if assumptions.get("tenure") == "rental":
        stabilized_value = noi / cap_rate
    else:
        stabilized_value = gross_revenue  # for condo, value = total sales
    results["stabilized_value"] = round(stabilized_value, 2)
    tags["stabilized_value"] = "derived_interpretation"

    # Step 7: Estimate hard construction costs
    # Hard cost = GFA * cost_per_m2 (varies by typology)
    hard_cost_per_m2 = assumptions.get("hard_cost_per_m2", 3500)
    tags["hard_cost_per_m2"] = "simulation_assumption"
    total_hard_cost = total_gfa_m2 * hard_cost_per_m2
    results["total_hard_cost"] = round(total_hard_cost, 2)

    # Step 8: Estimate soft costs
    # Soft costs = hard_cost * soft_cost_pct (typically 25-35%)
    soft_cost_pct = assumptions.get("soft_cost_pct", 0.30)
    total_soft_cost = total_hard_cost * soft_cost_pct
    results["total_soft_cost"] = round(total_soft_cost, 2)
    tags["soft_cost_pct"] = "simulation_assumption"

    # Step 9: Total development cost
    # TDC = hard + soft + land (if known)
    land_cost = assumptions.get("land_cost", 0)
    tags["land_cost"] = "simulation_assumption" if land_cost > 0 else "source_fact"
    total_development_cost = total_hard_cost + total_soft_cost + land_cost
    results["total_development_cost"] = round(total_development_cost, 2)

    # Step 10: Residual land value
    # RLV = Stabilized Value - TDC (excluding land) - Developer Profit
    developer_profit_pct = assumptions.get("developer_profit_pct", 0.15)
    developer_profit = stabilized_value * developer_profit_pct
    residual_land_value = stabilized_value - (total_hard_cost + total_soft_cost) - developer_profit
    results["residual_land_value"] = round(residual_land_value, 2)
    results["residual_land_value_per_m2"] = round(residual_land_value / parcel_area_m2, 2)
    tags["residual_land_value"] = "derived_interpretation"

    # Step 11: Return metrics summary
    # Yield on cost = NOI / TDC
    yield_on_cost = noi / total_development_cost if total_development_cost > 0 else 0
    # Cash-on-cash (simplified) = NOI / equity
    equity_pct = assumptions.get("equity_pct", 0.30)
    equity = total_development_cost * equity_pct
    cash_on_cash = noi / equity if equity > 0 else 0
    # Development spread = yield_on_cost - cap_rate
    development_spread = yield_on_cost - cap_rate

    results["return_metrics"] = {
        "yield_on_cost": round(yield_on_cost, 4),
        "cash_on_cash_return": round(cash_on_cash, 4),
        "development_spread": round(development_spread, 4),
        "cost_per_unit": round(total_development_cost / total_units, 2) if total_units else 0,
        "cost_per_m2_gfa": round(total_development_cost / total_gfa_m2, 2),
        "revenue_per_m2_gla": round(gross_revenue / sum(u["total_area_m2"] for u in unit_mix), 2) if unit_mix else 0,
    }

    results["value_tags"] = tags
    results["total_units"] = total_units
    results["total_gfa_m2"] = total_gfa_m2

    return results
```

---

## 14. Search Model

There are three search systems in this product:

### 1. Spatial Search

Find parcels matching geographic and dimensional criteria.

| Query Type | Implementation | Index |
|---|---|---|
| Parcels within area | `ST_Within(parcel.geom, search_area)` | GIST on `parcels.geom` |
| Parcels within radius | `ST_DWithin(parcel.geom::geography, point, radius_m)` | GIST on `parcels.geom` |
| Parcels matching frontage | `parcel.lot_frontage_m BETWEEN min AND max` | B-tree on `lot_frontage_m` |
| Parcels matching lot area | `parcel.lot_area_m2 BETWEEN min AND max` | B-tree on `lot_area_m2` |
| Parcels under specific zoning | `parcel.zone_code = ANY(:zones)` | B-tree on `zone_code` |
| Parcels near transit | Spatial join with `dataset_features` where `layer_type = 'transit'` | GIST |
| Parcels within overlays | Spatial join with overlay features | GIST |

### 2. Policy Search

Find applicable clauses and citations.

| Query Type | Implementation | Index |
|---|---|---|
| All clauses constraining height for a parcel | Policy resolution + `normalized_type = 'max_height'` | B-tree on `normalized_type` |
| All parking rules for a project type | Filter by `normalized_type` + `use_filter` applicability | GIN on `zone_filter` |
| Full-text policy search | `to_tsvector('english', raw_text) @@ to_tsquery(:query)` | GIN on `raw_text` tsvector |
| Semantic policy search | `embedding <=> :query_embedding ORDER BY` | IVFFlat on `embedding` |
| Clauses with citations | JOIN `policy_references` for cross-ref graph traversal | B-tree on foreign keys |

### 3. Opportunity Search

Reverse search for parcels matching a development thesis. Requires precomputed features.

| Feature | Computation | Storage |
|---|---|---|
| Zoning potential (max FSI) | Pre-resolve policy stack per parcel | `parcel_metrics` |
| Current underutilization | Compare existing built form vs. policy max | `parcel_metrics` |
| Precedent density | Count approved applications within 500m | `parcel_metrics` |
| Transit score | Distance to nearest high-frequency stop | `parcel_metrics` |
| Heritage/overlay flags | Spatial join with constraint layers | `parcel_metrics` |
| Market score | Average comp values in radius | `parcel_metrics` |
| Template compatibility | Can standard typology fit? (precomputed envelope check) | `parcel_metrics` |

Opportunity search query combines these precomputed features with user-specified thresholds for fast filtering without live simulation.

---

## 15. Data Flow Design

### A. Ingestion Flow

```text
1. Scheduled sync checks source endpoints (Celery Beat, nightly or weekly)
   -> Check Last-Modified / ETag headers against stored versions
2. Raw artifacts stored in S3 unchanged (keyed by SHA-256 of content)
   -> Deduplication: skip if hash matches existing object
3. Parsing extracts geometry, tables, clauses, references, and metadata
   -> PyMuPDF for PDF text extraction
   -> ogr2ogr / Fiona for GIS formats (SHP, GeoJSON)
   -> CSV parser with schema validation for tabular data
4. Validation checks schema, geometry validity, completeness, and confidence
   -> ST_IsValid() for geometry
   -> JSON Schema validation for extracted rules
   -> Confidence threshold check (< 0.85 -> review queue)
5. Normalization maps records into canonical entities
   -> Policy clauses -> normalized_json per ZoningRule schema
   -> Parcels -> standardized geometry in SRID 4326
   -> Applications -> standardized metadata
6. Search indexes updated
   -> OpenSearch bulk index for full-text
   -> pgvector embeddings for new clauses/rationales
   -> Materialized views for parcel_metrics refresh
7. New version snapshot published for online serving
   -> source_snapshots.is_active = true (atomically swap)
   -> Cache invalidation for affected parcels/policies
```

### B. Project Analysis Flow

```text
1. User selects parcel or address
   -> Geocode address to coordinates (Address Points dataset)
   -> Resolve parcel by ST_Contains(parcel.geom, point)
2. Geospatial service resolves parcel set and jurisdiction
   -> Multi-parcel assembly via ST_Union if multiple parcels
   -> Determine jurisdiction from parcel geometry
3. Policy service resolves applicable policy stack
   -> Query policy_applicability_rules by geometry + zone
   -> Apply override hierarchy (site-specific > overlay > area > base > OP)
   -> Return ordered list of applicable rules with citations
4. Dataset service loads overlays and source facts
   -> Heritage, floodplain, transit, environmental via spatial joins
5. Simulation service generates buildable envelope and candidate massing
   -> Envelope generation algorithm (Section 13)
   -> Multiple massing templates if requested
6. Layout service generates floor-plate scenarios
   -> Unit mix optimization (Section 13)
7. Finance service produces viability outputs
   -> Pro forma calculation (Section 13)
8. Entitlement and precedent services evaluate compliance
   -> Entitlement scoring (Section 13)
9. All outputs saved against versioned scenario snapshot
   -> Immutable: scenario_run.input_hash frozen
   -> source_snapshot_id recorded for reproducibility
10. Export materialized asynchronously if requested
    -> Celery task for PDF/CSV/XLSX generation
```

### C. Variance Simulation Flow

```text
1. User creates a scenario fork
   -> New scenario_run with parent_scenario_id pointing to base
   -> scenario_type = 'variance'
2. Requested overrides attached to the new scenario
   -> project_policy_override records created
   -> Override values stored as modified ZoningRule JSON
3. Policy engine produces alternate interpreted rule stack
   -> Re-resolve with overrides applied at highest precedence
   -> Track delta between base and variant rule stacks
4. Simulation reruns against modified rule set
   -> New envelope, new massing, new layout
   -> Same parcel, different constraints
5. Entitlement and precedent scoring rerun with new deltas
   -> Compliance score reflects variance magnitude
   -> Precedent search refocused on similar variance cases
6. Result stored as sibling scenario, never destructive overwrite
   -> Both base and variant scenario_runs preserved
   -> Delta comparison available via result_json diff
```

---

## 16. API Design

### Endpoints

```text
# --- Projects ---
POST   /api/v1/projects                           # Create project
GET    /api/v1/projects/{id}                       # Get project details
PATCH  /api/v1/projects/{id}                       # Update project
POST   /api/v1/projects/{id}/parcels               # Add parcels to project
DELETE /api/v1/projects/{id}/parcels/{parcel_id}   # Remove parcel

# --- Parcels ---
GET    /api/v1/parcels/search                      # Search parcels (spatial, zoning, opportunity)
GET    /api/v1/parcels/{id}                        # Get parcel details
GET    /api/v1/parcels/{id}/policy-stack            # Resolved policy stack with citations
GET    /api/v1/parcels/{id}/overlays                # Dataset overlays for parcel

# --- Scenarios ---
POST   /api/v1/projects/{id}/scenarios             # Create scenario (base or variance)
GET    /api/v1/scenarios/{id}                      # Get scenario details + status
GET    /api/v1/scenarios/{id}/compare/{other_id}   # Compare two scenarios

# --- Simulation ---
POST   /api/v1/scenarios/{id}/massings             # Generate massing (async -> 202)
GET    /api/v1/massings/{id}                       # Get massing result
POST   /api/v1/massings/{id}/layout-runs           # Run unit mix optimization (async -> 202)
GET    /api/v1/layout-runs/{id}                    # Get layout result

# --- Finance ---
POST   /api/v1/scenarios/{id}/financial-runs       # Run pro forma (async -> 202)
GET    /api/v1/financial-runs/{id}                 # Get financial result

# --- Entitlement ---
POST   /api/v1/scenarios/{id}/entitlement-runs     # Run entitlement check (async -> 202)
GET    /api/v1/entitlement-runs/{id}               # Get entitlement result

# --- Precedent ---
POST   /api/v1/scenarios/{id}/precedent-searches   # Search precedents (async -> 202)
GET    /api/v1/precedent-searches/{id}             # Get precedent results

# --- Policy ---
GET    /api/v1/policies/search                     # Full-text + semantic policy search
POST   /api/v1/scenarios/{id}/policy-overrides     # Add policy override to scenario

# --- Exports ---
POST   /api/v1/exports                            # Request export (async -> 202)
GET    /api/v1/exports/{id}                        # Get export status + download URL

# --- Jobs ---
GET    /api/v1/jobs/{id}                           # Poll job status (for any async operation)

# --- Admin ---
GET    /api/v1/organizations/{id}/audit-log        # Audit trail
GET    /api/v1/admin/ingestion-jobs                # Ingestion job status
POST   /api/v1/admin/ingestion-jobs/{id}/retry     # Retry failed ingestion
```

### API Design Rules

1. **Idempotency**: Every `POST` endpoint accepts an `Idempotency-Key` header. Duplicate requests with the same key return the original response.

2. **Async jobs (202 Accepted)**: Any operation that may take > 1 second returns `202 Accepted` with a `Location` header pointing to the job/result resource. Client polls or uses webhooks.

3. **Source citations**: Every derived output response includes a `_citations` array with:
   ```json
   {
     "_citations": [
       {
         "source_clause_id": "uuid",
         "source_document": "Zoning By-law 569-2013",
         "section_ref": "40.10.40.10",
         "confidence": 0.97,
         "source_snapshot_id": "uuid"
       }
     ]
   }
   ```

4. **Explicit scenarios**: Scenario creation is always explicit — never hidden inside mutable updates. Every simulation result is tied to a specific `scenario_run_id`.

5. **Pagination**: List endpoints use cursor-based pagination (`?cursor=<opaque>&limit=50`).

6. **Filtering**: Search endpoints accept structured filter objects as query parameters or POST body.

---

## 17. Infrastructure

### Docker Compose (Local Development)

```yaml
version: "3.9"
services:
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://arterial:arterial@db:5432/arterial
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_BUCKET: arterial-docs
      AWS_ACCESS_KEY_ID: minioadmin
      AWS_SECRET_ACCESS_KEY: minioadmin
      OPENSEARCH_URL: http://opensearch:9200
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    volumes:
      - .:/app
    depends_on:
      - db
      - redis
      - minio
      - opensearch

  worker:
    build: .
    command: celery -A app.worker worker --loglevel=info --concurrency=4
    environment:
      DATABASE_URL: postgresql://arterial:arterial@db:5432/arterial
      REDIS_URL: redis://redis:6379/0
      S3_ENDPOINT: http://minio:9000
      S3_BUCKET: arterial-docs
      AWS_ACCESS_KEY_ID: minioadmin
      AWS_SECRET_ACCESS_KEY: minioadmin
      OPENSEARCH_URL: http://opensearch:9200
      CLAUDE_API_KEY: ${CLAUDE_API_KEY}
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  beat:
    build: .
    command: celery -A app.worker beat --loglevel=info
    environment:
      DATABASE_URL: postgresql://arterial:arterial@db:5432/arterial
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis

  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: arterial
      POSTGRES_USER: arterial
      POSTGRES_PASSWORD: arterial
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-extensions.sql:/docker-entrypoint-initdb.d/01-extensions.sql

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - miniodata:/data

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    environment:
      discovery.type: single-node
      DISABLE_SECURITY_PLUGIN: "true"
      OPENSEARCH_JAVA_OPTS: "-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - osdata:/usr/share/opensearch/data

volumes:
  pgdata:
  miniodata:
  osdata:
```

### Railway MVP Deployment

| Service | Railway Service Type | Estimated Monthly Cost |
|---|---|---|
| API (FastAPI) | Web Service (1 vCPU, 1GB) | $5–10 |
| Worker (Celery) | Worker Service (1 vCPU, 2GB) | $10–15 |
| PostgreSQL + PostGIS | Railway Postgres plugin | $5–15 (1GB storage) |
| Redis | Railway Redis plugin | $5 |
| Object Storage | Cloudflare R2 (external, free tier 10GB) | $0–5 |
| OpenSearch | Skip for MVP; use PostgreSQL full-text | $0 |
| **Total MVP** | | **$25–50/month** |

Railway caveats:
- No native PostGIS support in Railway Postgres — use a Docker service with the `postgis/postgis` image instead.
- No native OpenSearch — defer to PostgreSQL `tsvector` full-text search for MVP. Add OpenSearch when query volume justifies it.
- Acceptable for internal prototype and short-lived demo. Not preferred for production with heavy spatial workloads and long-running jobs.

### AWS / GCP Growth Path

| Component | AWS | GCP | Estimated Monthly Cost |
|---|---|---|---|
| API + Workers | ECS Fargate (2 services) | Cloud Run | $50–150 |
| PostgreSQL + PostGIS | RDS PostgreSQL with PostGIS | Cloud SQL | $50–200 |
| Redis | ElastiCache | Memorystore | $30–50 |
| Object Storage | S3 | Cloud Storage | $5–20 |
| Search | OpenSearch Service | Elastic Cloud | $50–150 |
| Workflow | Temporal Cloud or self-hosted | Temporal Cloud | $0–100 |
| CI/CD | GitHub Actions | GitHub Actions | $0–15 |
| Monitoring | CloudWatch + Grafana Cloud | Cloud Monitoring + Grafana | $0–50 |
| **Total Growth** | | | **$185–735/month** |

### Scaling Strategy from Day 1

| Concern | Day 1 (MVP) | Growth | Scale |
|---|---|---|---|
| Compute | Single API + single worker | Separate API and worker scaling | Auto-scaled worker pools per task type |
| Database | Single Postgres instance | Read replicas for search-heavy queries | Partition by jurisdiction |
| Search | PostgreSQL tsvector + pgvector | Add OpenSearch for full-text | Dedicated OpenSearch cluster |
| Object Storage | MinIO (local) / R2 (deploy) | S3 with lifecycle policies | S3 + CloudFront CDN for exports |
| Async | Celery + Redis | Celery with priority queues | Temporal for workflow orchestration |
| Caching | Redis single instance | Redis cluster with cache-aside | Multi-layer: local + Redis + CDN |

---

## 18. Observability

### Telemetry Requirements

| Metric | Why | Tool |
|---|---|---|
| Request tracing across API and worker paths | Debug latency, identify bottlenecks | OpenTelemetry + Jaeger/Tempo |
| Job duration and failure metrics | SLA monitoring, capacity planning | Prometheus + Grafana |
| Parser confidence distributions | Data quality monitoring | Custom metrics -> Prometheus |
| Refresh lag by source | Freshness monitoring | Celery Beat heartbeat + custom gauge |
| Simulation input hashes | Reproducibility verification | Logged per scenario_run |
| Source snapshot IDs used in each analysis | Audit trail | Stored in scenario_run.source_snapshot_id |
| API latency percentiles (p50, p95, p99) | Performance SLAs | OpenTelemetry -> Prometheus |
| Error rates by endpoint and error type | Reliability monitoring | Sentry + Prometheus |
| Database query performance | Slow query detection | pg_stat_statements + Grafana |
| Queue depth and worker utilization | Capacity planning | Celery Flower + Prometheus |

### Recommended Tooling

| Category | Tool | Notes |
|---|---|---|
| Distributed tracing | OpenTelemetry SDK -> Jaeger or Grafana Tempo | Instrument FastAPI with `opentelemetry-instrumentation-fastapi` |
| Metrics | Prometheus + Grafana | `prometheus-fastapi-instrumentator` for auto-instrumentation |
| Structured logging | structlog -> stdout -> Loki or CloudWatch | JSON logs with trace_id, request_id, org_id |
| Error tracking | Sentry | `sentry-sdk[fastapi]` for auto-capture |
| Uptime monitoring | Grafana Synthetic Monitoring or UptimeRobot | Health check endpoint: `GET /health` |
| Celery monitoring | Flower (MVP) -> Prometheus exporter | `celery-prometheus-exporter` |

---

## 19. Scalability

### Partitioning Strategy

| Data | Partition Key | Method |
|---|---|---|
| Parcels | `jurisdiction_id` | Table partitioning (PostgreSQL declarative) |
| Policy clauses | `jurisdiction_id` via `policy_version` | Logical partitioning |
| Dataset features | `dataset_layer_id` | Range partitioning by layer |
| Development applications | `jurisdiction_id` | Table partitioning |
| Audit events | `created_at` (monthly) | Range partitioning |
| Source snapshots | `jurisdiction_id` + `snapshot_type` | Logical grouping |

### Caching Strategy

| Cache Target | TTL | Invalidation |
|---|---|---|
| Parcel summaries | 24 hours | On parcel data refresh |
| Policy stacks (by parcel set + snapshot) | Until snapshot change | On new policy_version publish |
| Frequently used overlay queries | 1 hour | On dataset refresh |
| Precedent retrieval results | 12 hours | On new application ingestion |
| Export artifacts | 7 days | Never (immutable, signed URL expires) |
| Geocoding results | 30 days | On address data refresh |

### Async Job Design

Anything that can take more than roughly one second must be a background job:

- OCR and document extraction
- Policy clause extraction (Claude API calls)
- Batch parcel feature generation (opportunity search precompute)
- Heavy massing runs
- Layout optimization (LP solver)
- Precedent interpretation
- Financial model computation
- Report export (PDF/XLSX generation)

Job priority queues:
```
high:    user-initiated simulation, entitlement check
medium:  export generation, precedent search
low:     batch parcel feature refresh, ingestion
```

### Reliability Controls

- **Idempotent ingestion jobs**: Use file hash + source URL as natural dedup key.
- **Retry with exponential backoff**: 3 retries, 1s / 4s / 16s delays.
- **Dead-letter handling**: Failed jobs after max retries go to DLQ for manual review.
- **Immutable scenario outputs**: `scenario_run` + `input_hash` are never modified.
- **Rollbackable policy publishes**: `policy_versions.is_active` flag; swap atomically, keep old version.
- **Workflow state visibility**: All job statuses queryable via `GET /api/v1/jobs/{id}`.
- **Health checks**: Readiness probe checks DB + Redis connectivity.

---

## 20. Implementation Phases

### Phase 1: Strong MVP

**Goal**: Trustworthy parcel + policy + envelope foundation for one city.

Build:
- [ ] Docker Compose development stack (PostgreSQL + PostGIS, Redis, MinIO, API, Worker)
- [ ] PostgreSQL schema with PostGIS and pgvector extensions
- [ ] Organization, auth (JWT), user, project, and scenario tables
- [ ] Toronto parcel ingestion (Property Boundaries -> parcels table)
- [ ] Toronto zoning geometry ingestion (By-law 569-2013 map -> zone_code linkage)
- [ ] Address geocoding (Address Points dataset)
- [ ] Parcel lookup by address, coordinates, and PIN
- [ ] Basic parcel-to-zoning and overlay resolution
- [ ] Policy document ingestion pipeline (PDF -> S3 -> PyMuPDF -> clauses)
- [ ] LLM-assisted clause extraction (Claude API -> normalized ZoningRule JSON)
- [ ] Confidence scoring and review queue for low-confidence extractions
- [ ] Policy versioning and publish snapshots
- [ ] Effective policy stack resolution API with citations
- [ ] Deterministic envelope generation (basic: setbacks, height, lot coverage, FAR)
- [ ] Scenario persistence with immutable input hashes
- [ ] Simple PDF and CSV export
- [ ] Basic API endpoints (projects, parcels, policy-stack, scenarios, massings)
- [ ] CI/CD with GitHub Actions (lint, test, build)

Do not build yet: full precedent scoring, AI HBU generation, advanced layout optimization, construction-cost modeling depth.

### Phase 2: Decision Engine

**Goal**: Add financial viability and layout optimization.

Build:
- [ ] Unit type library for Toronto market
- [ ] Unit mix optimizer (OR-Tools LP)
- [ ] Floor-plate scenario generation
- [ ] Market comparable ingestion (structure for licensed data)
- [ ] Financial assumption sets (user-configurable)
- [ ] Pro forma engine (11-step calculation)
- [ ] Basic entitlement checks (rule-by-rule compliance)
- [ ] Development application ingestion (Toronto Open Data)
- [ ] Precedent retrieval (spatial + form similarity)
- [ ] Rationale extraction from staff reports (Claude API)
- [ ] Explainable entitlement scoring (6-feature model)
- [ ] Async job infrastructure hardening (priority queues, DLQ)
- [ ] OpenSearch integration for full-text policy search
- [ ] Railway deployment for demo/staging

### Phase 3: Competitive Differentiation

**Goal**: Variance simulation, opportunity search, multi-jurisdiction readiness.

Build:
- [ ] Variance simulation workflow (scenario fork, re-resolve, compare)
- [ ] Approval probability models (calibrated on CoA + OLT decisions)
- [ ] Reverse parcel search (opportunity search with precomputed features)
- [ ] Batch parcel feature precomputation pipeline
- [ ] Organization templates (saved assumption sets, unit libraries)
- [ ] Multi-jurisdiction abstraction (jurisdiction-aware parser config)
- [ ] Second city pilot (e.g., Vancouver or Ottawa)
- [ ] Advanced angular plane and stepback support
- [ ] Webhook support for async job completion notifications
- [ ] pgvector -> HNSW index migration for scale

### Phase 4: Enterprise Hardening

**Goal**: Production-grade security, reliability, and scale.

Build:
- [ ] SSO/SAML integration
- [ ] Granular RBAC permissions (row-level organization isolation)
- [ ] Temporal migration for workflow orchestration
- [ ] OpenSearch cluster hardening
- [ ] Caching strategy implementation (Redis cluster, cache-aside pattern)
- [ ] Load testing and performance optimization
- [ ] Dataset marketplace or custom source onboarding
- [ ] Tenant-specific models and templates
- [ ] SLA-backed refresh pipelines
- [ ] Data retention and compliance policies
- [ ] Full audit trail and compliance reporting
- [ ] AWS/GCP production deployment with IaC (Terraform)

---

## 21. Testing & Verification

### Unit Tests

| Domain | Test Coverage |
|---|---|
| Policy normalization | Bylaw text -> canonical ZoningRule JSON for known samples |
| Policy resolution | Given parcel + zone, correct rules returned in correct precedence |
| Envelope generation | Given parcel geometry + rules, correct setbacks/height/FAR/coverage |
| Unit mix optimization | LP solver produces feasible, optimal allocations |
| Financial calculations | Pro forma arithmetic matches hand-calculated expected values |
| Entitlement scoring | Feature computation produces expected scores for known inputs |
| Geocoding | Address -> parcel linkage for known Toronto addresses |

### Integration Tests

| Flow | Test |
|---|---|
| Address -> parcel -> policy stack | End-to-end: input address, get correct zoning rules with citations |
| Parcel -> envelope | Parcel geometry + resolved rules -> valid 2D/3D envelope |
| Envelope -> unit mix | Envelope GLA -> unit mix optimizer -> valid allocation |
| Unit mix -> finance | Unit mix + assumptions -> pro forma with correct metrics |
| Scenario fork -> variance delta | Base scenario + override -> new scenario with correct deltas |
| Ingestion -> search | Ingest source -> clauses searchable in full-text and vector |

### Data Quality Tests

| Check | Implementation |
|---|---|
| Geometry validity | `ST_IsValid(geom)` for all parcels and features on ingestion |
| Source completeness | Assert non-null for required fields per source schema |
| Parser schema validation | Validate every `normalized_json` against ZoningRule JSON Schema |
| Citation presence | Assert every `policy_clause` has a `section_ref` and `source_clause_id` |
| Source snapshot consistency | Assert every active scenario references a valid, active source_snapshot |
| Duplicate detection | Assert uniqueness of `(jurisdiction_id, pin)` for parcels |

### Accuracy Tests

| Test | Method |
|---|---|
| Extracted rules vs. known bylaws | Manually verify 50+ extracted rules against known By-law 569-2013 sections |
| Envelope outputs vs. hand-checked scenarios | Compare generated envelopes against architect-verified zoning scenarios for 10 known parcels |
| Precedent retrieval quality | Evaluate precision/recall on 20 known development applications |
| Financial outputs vs. spreadsheet | Compare pro forma outputs against analyst-prepared spreadsheets for 5 test projects |

### Performance Tests

| Test | Target |
|---|---|
| Spatial query concurrency | 50 concurrent parcel searches < 200ms p95 |
| Policy stack resolution | Single parcel policy stack < 500ms |
| Envelope generation | Single parcel envelope < 2s |
| Unit mix optimization | LP solve < 5s for 200-unit building |
| Background job throughput | Worker processes 100 parcels/minute for batch feature precompute |
| Export generation latency | PDF report < 10s, XLSX < 5s |
| Cache hit effectiveness | > 80% cache hit rate for repeated parcel/policy queries |

### Governance Tests

| Test | Method |
|---|---|
| License enforcement | Restricted-source data excluded from export outputs |
| Audit trail completeness | Every user action produces an `audit_event` record |
| RBAC enforcement | Cross-organization data access returns 403 |
| Source attribution | Every exported report includes source citations |

### Security Tests

| Test | Method |
|---|---|
| SQL injection | Parameterized queries; test with OWASP payloads |
| Authentication bypass | Verify JWT validation on all protected endpoints |
| Tenant isolation | Verify organization_id filtering on all queries |
| Signed URL expiry | Verify expired signed URLs return 403 |

---

## 22. Biggest Risks

### 1. Policy Normalization Risk

**Risk**: If we cannot reliably transform bylaws into canonical rules, downstream simulation and compliance become brittle.

**Mitigation**:
- Start with the most structured sections of By-law 569-2013 (zone standards have predictable table formats).
- Use Claude API extraction with few-shot examples tailored to Toronto bylaw format.
- Confidence scoring: route anything < 0.85 to human review before publishing.
- Maintain raw text alongside normalized rules so humans can always verify.
- Build a test suite of 50+ manually verified rule extractions for regression testing.

### 2. Data Licensing Risk

**Risk**: Private comparable data (MLS, MPAC) and some city datasets may constrain reuse, storage, and export.

**Mitigation**:
- Track `license_status` per dataset and enforce at the export layer.
- Design the financial model to work with user-supplied assumptions when licensed comps are unavailable.
- Use CMHC aggregate data as a free fallback for rental market signals.
- Legal review before integrating any restricted data source.

### 3. Explainability Risk

**Risk**: Users in this domain will not trust opaque outputs. If they cannot trace results back to source text, assumptions, and scenarios, adoption fails.

**Mitigation**:
- 4-layer explainability model enforced in every output (Section 5).
- Every API response includes `_citations` array.
- `value_tags` in financial outputs distinguish market-derived vs. assumed values.
- Source snapshot IDs stored on every scenario for reproducibility.

### 4. Jurisdiction Expansion Risk

**Risk**: Toronto is only the MVP. Rules differ dramatically across cities. Future cities will vary in source formats, terminology, and rule semantics.

**Mitigation**:
- All models are jurisdiction-scoped (`jurisdiction_id` on every major table).
- Parser configuration is per-jurisdiction (different extraction prompts, schemas).
- Canonical rule types are designed to be cross-jurisdictional (height, setback, FAR are universal concepts).
- Test with a second city in Phase 3 to validate abstraction before scaling further.

### 5. Geometry Edge-Case Risk

**Risk**: Irregular lots, easements, missing frontage information, conflicting overlays, and incomplete data will produce hard simulation failures.

**Mitigation**:
- Edge classification algorithm uses road network matching, not just geometry angles.
- Envelope generation gracefully degrades: if a step fails, return partial result with compliance notes.
- `parcel_metrics` precomputation catches invalid geometries (`ST_IsValid`) before they enter simulation.
- Manual override support: users can specify edge types and setbacks when auto-detection fails.
- Test against the 20 most irregular parcel shapes in Toronto to catch edge cases early.

---

## 23. Tech Stack Summary

| Layer | Technology | Purpose |
|---|---|---|
| **API Framework** | FastAPI (Python 3.11+) | REST API, async request handling, auto-generated OpenAPI docs |
| **ORM / DB Access** | SQLAlchemy 2.0 + GeoAlchemy2 | ORM with PostGIS geometry support |
| **Validation** | Pydantic v2 | Request/response validation, settings management |
| **Database** | PostgreSQL 16 + PostGIS 3.4 | Transactional data, spatial queries, geometry storage |
| **Vector Search** | pgvector | Semantic similarity search for clauses, rationales, precedents |
| **Cache / Broker** | Redis 7 | Caching, distributed locks, Celery message broker |
| **Object Storage** | S3 / MinIO / Cloudflare R2 | Raw documents, OCR artifacts, exports, 3D files |
| **Full-Text Search** | OpenSearch 2.x (PostgreSQL tsvector for MVP) | Clause search, document retrieval, faceted filtering |
| **Async Workers** | Celery (MVP) -> Temporal (growth) | Background jobs: parsing, simulation, export |
| **Scheduled Jobs** | Celery Beat (MVP) -> Dagster (growth) | Data refresh, batch precomputation |
| **Geometry (2D)** | Shapely 2.x | Polygon operations, setback/buffer, intersection, area |
| **Geometry (3D)** | Trimesh | 3D mesh generation, extrusion, export (GLB/OBJ) |
| **Numeric** | NumPy, SciPy | Array math, statistical calculations |
| **Optimization** | OR-Tools (Google) | Linear programming for unit mix optimization |
| **PDF Parsing** | PyMuPDF (fitz) | PDF text extraction, page segmentation |
| **OCR Fallback** | Tesseract (pytesseract) | Scanned document text extraction |
| **LLM** | Claude API (Anthropic) | Clause extraction, rationale summarization, semantic search |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) | Vector embeddings for policy clauses and precedent rationales |
| **GIS Formats** | Fiona, pyproj, rasterio | SHP/GeoJSON parsing, CRS transformation |
| **PDF Export** | WeasyPrint | HTML -> PDF report generation |
| **Spreadsheet Export** | openpyxl | XLSX pro forma and data export |
| **Auth** | python-jose (JWT) | Token-based authentication |
| **Rate Limiting** | slowapi | Per-user and per-org rate limiting |
| **HTTP Client** | httpx | Async HTTP for data source fetching |
| **CI/CD** | GitHub Actions | Lint, test, build, deploy |
| **IaC** | Terraform (Phase 4) | Infrastructure as code for AWS/GCP |
| **Monitoring** | OpenTelemetry, Prometheus, Grafana, Sentry | Tracing, metrics, logging, error tracking |
| **Containerization** | Docker, Docker Compose | Local dev environment, deployment images |

---

## 24. Sources

### Arterial Product References

- https://www.arterial.design/
- https://docs.arterial.design/
- https://docs.arterial.design/essentials/projects
- https://docs.arterial.design/essentials/policies
- https://docs.arterial.design/essentials/datasets
- https://docs.arterial.design/essentials/massing
- https://docs.arterial.design/essentials/layout
- https://docs.arterial.design/essentials/entitlements
- https://docs.arterial.design/essentials/finances
- https://docs.arterial.design/workflows/simulation
- https://docs.arterial.design/workflows/entitlement
- https://docs.arterial.design/workflows/exporting
- https://docs.arterial.design/workflows/upzoning

### Toronto Open Data

- https://open.toronto.ca/ (Portal)
- https://open.toronto.ca/dataset/zoning-by-law-569-2013-zoning-area-map/
- https://open.toronto.ca/dataset/property-boundaries/
- https://open.toronto.ca/dataset/address-points-municipal-toronto-one-address-repository/
- https://open.toronto.ca/dataset/development-applications/
- https://open.toronto.ca/dataset/building-permits-active-permits/
- https://open.toronto.ca/dataset/building-permits-cleared-permits/
- https://open.toronto.ca/dataset/committee-of-adjustment-decisions/
- https://open.toronto.ca/dataset/heritage-register/
- https://open.toronto.ca/dataset/ravine-and-natural-feature-protection/
- https://open.toronto.ca/dataset/neighbourhoods/
- https://open.toronto.ca/dataset/city-wards/
- https://open.toronto.ca/dataset/3d-massing/
- https://open.toronto.ca/dataset/toronto-centreline-tcl/
- https://open.toronto.ca/dataset/parks/
- https://open.toronto.ca/dataset/ttc-routes-and-schedules/

### City of Toronto Planning

- https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/zoning-by-law-569-2013-2/
- https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/
- https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/chapter-6-secondary-plans/
- https://gis.toronto.ca/arcgis/rest/services

### External Data Sources

- https://trca.ca/conservation/flood-risk-management/flood-plain-map-viewer/ (TRCA Floodplain)
- https://www.olt.gov.on.ca/decisions-and-orders/ (Ontario Land Tribunal)

### Technology Documentation

- PostgreSQL: https://www.postgresql.org/docs/16/
- PostGIS: https://postgis.net/docs/
- pgvector: https://github.com/pgvector/pgvector
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Shapely: https://shapely.readthedocs.io/
- Trimesh: https://trimesh.org/
- OR-Tools: https://developers.google.com/optimization
- PyMuPDF: https://pymupdf.readthedocs.io/
- Celery: https://docs.celeryq.dev/
- OpenTelemetry: https://opentelemetry.io/docs/
- Claude API: https://docs.anthropic.com/
