# Deep Analysis: Arterial.design Clone — Backend, Data, and Infrastructure Plan

## Context

We are building a clone of [Arterial](https://www.arterial.design/) as a land-development due diligence platform. The focus of this plan is backend architecture, data pipelines, policy processing, simulation, and scalable infrastructure. UI is intentionally out of scope.

The original Arterial project link shared for reference appears access-locked without an authenticated session, so this plan is based on Arterial's public product and documentation footprint plus Toronto-specific MVP assumptions.

## Executive Summary

Arterial is best understood as five backend systems working together:

1. A geospatial parcel and map platform
2. A versioned policy and citation graph
3. A deterministic geometry and simulation engine
4. A precedent retrieval and entitlement scoring engine
5. A comparable-driven financial modeling engine

If we build only a zoning lookup or only a parcel search tool, we will miss the real value. The core of the product is the ability to turn a parcel into a defendable development scenario with citations, assumptions, geometry, and viability outputs.

## Key Decisions

- Scope: single-city MVP, Toronto
- Product focus: backend-first, trustworthy policy resolution, scalable async analysis
- Compliance philosophy: deterministic rule engine is the source of truth
- AI philosophy: use LLMs for extraction, retrieval, summarization, and analyst assistance, but not as the final authority for legal compliance or geometry
- Infrastructure direction: local Docker Compose for development, managed cloud services for production, avoid premature microservices

## Guiding Principles

### 1. Deterministic beats plausible

Policy resolution, massing calculations, and financial computations must be reproducible. LLM output can help extract or rank information, but final answers need structured rules and deterministic evaluation.

### 2. Every output must be explainable

Every result should separate:

- source facts
- derived rule interpretations
- simulation assumptions
- model predictions

This is essential for user trust, debugging, and enterprise adoption.

### 3. Version everything

We must version:

- raw source files
- parsed policy text
- normalized rules
- dataset refreshes
- simulation inputs
- model versions
- exported reports

If a user reruns the same scenario later, we should be able to explain why the output changed or prove that it did not.

### 4. Design for long-running analysis

This product is not simple CRUD. OCR, parsing, massing, layout optimization, entitlement analysis, and report generation are all background jobs. The architecture must treat async work as a first-class concern from day one.

### 5. Build a strong Toronto MVP before generalizing

Toronto is a good first city because the public data ecosystem is relatively strong. But the architecture should still assume that each future jurisdiction will have different terminology, source quality, and policy structure.

## What We Are Building

### Core product modules

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

### Primary users

- development analysts
- planners
- architects
- acquisitions teams
- entitlement consultants
- real estate finance teams
- organization admins

### Core user jobs to be done

1. Find parcels worth analyzing.
2. Pull the full applicable policy stack for a site.
3. Determine what is allowed as-of-right.
4. Generate a buildable envelope and massing options.
5. Turn massing into unit or area scenarios.
6. Estimate financial viability.
7. Review precedents and approval risk.
8. Export a shareable due diligence package.

## Toronto MVP Data Sources

The MVP should intentionally target Toronto and use a constrained set of sources we can operationalize well.

### Core Toronto data sources

- Zoning Bylaw 569-2013 from Toronto Open Data
- zoning schedules and amendment datasets from Toronto Open Data
- parcel or property geometry from Toronto GIS / open data sources
- official plan and secondary plan documents from City of Toronto sources
- development application tracking data from Toronto Open Data
- OGC WMS / GIS layers from the city's geospatial services

### Strong Toronto enrichment sources

- transit layers
- heritage layers
- floodplain and environmental constraints
- road network and frontage context
- neighborhood amenity layers
- market comparables from licensed external providers where allowed

### Important note on licensed data

Some of the most valuable financial and comparable data is not fully open:

- MLS-derived data
- private rent or sales feeds
- construction cost subscriptions
- assessment datasets with usage restrictions

We should assume these require explicit licensing review before ingestion, storage, or export.

## Data Requirements

### 1. Policy and regulatory data

We need:

- zoning bylaws
- zoning maps
- official plans
- secondary plans
- area-specific guidelines
- urban design guidelines
- policy amendments and effective dates
- site-specific exceptions and overlays

### 2. Parcel and cadastral data

We need:

- parcel boundaries
- addresses and geocoder support
- parcel identifiers
- lot area, depth, frontage
- current land use where available
- assessed value or market signal where legally available
- parcel-to-jurisdiction mapping

### 3. Development application and precedent data

We need:

- application metadata
- location and parcel linkage
- application type
- current status
- approval or denial outcome
- staff reports
- planning rationales
- supporting drawings or attachments
- board or tribunal decisions where available

### 4. Financial and market data

We need:

- rent comps by unit type
- sale comps by unit type or asset class
- construction cost references
- cap rates
- operating expense assumptions
- absorption and vacancy assumptions

### 5. GIS overlays

We need:

- transit
- roads
- heritage
- environmental constraints
- floodplains
- infrastructure-related overlays
- neighborhood and amenity context

### Metadata we must store for every source

- source URL
- publisher
- acquisition timestamp
- effective date
- jurisdiction
- geometry CRS/SRID
- parser version
- extraction confidence
- license status
- lineage back to the original file

## Policy And Data Governance Requirements

These requirements are non-optional if the platform is meant to be trusted.

### External data policy requirements

- track license status for every dataset and document
- track whether redistribution is allowed
- track whether exports may include derived values from licensed data
- retain source attribution in user-facing outputs

### Internal governance requirements

- freeze source versions used in every analysis
- never let LLM output become policy truth without validation
- route low-confidence extractions into review workflows
- support rollback of bad policy refreshes
- log all manual policy overrides

### Security and privacy requirements

- organization-scoped RBAC
- row-level tenant isolation
- encryption at rest and in transit
- signed URLs for private files
- audit logs for exports and shared reports
- managed secret storage

## Inputs And Outputs

### User inputs

| Input | Type | Used By |
|---|---|---|
| Parcel address, coordinates, or PIN | Text / map / API | Parcel resolution, jurisdiction lookup, all downstream modules |
| Project boundary | Geometry or parcel set | Multi-parcel assembly and simulation |
| Development program | Structured form or API payload | Massing, layout, finance |
| Massing assumptions | Structured parameters | Simulation engine |
| Policy overrides | Structured scenario inputs | Variance simulation |
| Search filters | Structured form | Parcel search and opportunity screening |
| Financial assumptions | Structured form | Pro forma |
| Precedent search filters | Structured form | Entitlement and precedent engine |
| Export preferences | Structured form | Report generation |

### User outputs

| Output | Type | Module |
|---|---|---|
| Parcel summary | Structured JSON | Geospatial service |
| Effective policy stack | Structured JSON + citations | Policy engine |
| Applicable regulations | Clause list + normalized rules + source refs | Policy engine |
| As-of-right envelope | Geometry + metrics | Simulation engine |
| Candidate massings | Geometry + metrics + assumptions | Simulation engine |
| Unit mix scenarios | Structured tables | Layout optimizer |
| Financial outputs | Structured metrics and assumptions | Finance engine |
| Entitlement results | Rule-by-rule checks + rationale | Entitlement engine |
| Comparable precedents | Search results + supporting evidence | Precedent engine |
| Variance delta analysis | Before/after scenario comparison | Scenario engine |
| Export package | PDF / CSV / spreadsheet / 3D artifacts | Export service |

## Functional Domains And Service Responsibilities

### 1. Project and tenant domain

Responsibilities:

- organizations
- users
- workspaces
- projects
- project sharing
- templates
- audit history

### 2. Geospatial domain

Responsibilities:

- parcel lookup
- geometry storage
- adjacency and frontage calculations
- spatial joins
- overlay retrieval
- map tile or geometry-serving support

### 3. Policy domain

Responsibilities:

- raw document storage
- clause extraction
- cross-reference resolution
- normalized rule generation
- policy applicability resolution
- versioning and citation support

### 4. Dataset domain

Responsibilities:

- ingest non-policy layers
- maintain source lineage
- refresh schedules
- parcel overlay linking
- feature filtering

### 5. Simulation domain

Responsibilities:

- envelope generation
- massing generation
- scenario revisioning
- compliance delta computation

### 6. Layout optimization domain

Responsibilities:

- unit libraries
- area allocation
- dimensional constraints
- floor-plate level scenario generation

### 7. Finance domain

Responsibilities:

- market comparable ingestion
- user assumption sets
- revenue and cost modeling
- valuation metrics

### 8. Entitlement and precedent domain

Responsibilities:

- project-to-policy comparison
- precedent retrieval
- rationale summarization
- explainable risk scoring

### 9. Export domain

Responsibilities:

- PDF generation
- CSV and spreadsheet export
- 3D export packaging
- report versioning

### 10. Ingestion and orchestration domain

Responsibilities:

- scheduled source refreshes
- parsing pipelines
- validation workflows
- publish new snapshots for online use

## Policy Processing Pipeline

This is the hardest and most defensible part of the product.

### Required pipeline

```text
Raw Source File (PDF / HTML / GIS / CSV)
  -> Immutable raw storage
  -> Parsing and OCR
  -> Section and clause segmentation
  -> LLM-assisted extraction
  -> Canonical normalization
  -> Validation and confidence scoring
  -> Human review for low-confidence outputs
  -> Versioned policy graph
  -> Online policy resolution
```

### Policy modeling rules

We must store both:

- raw legislative text
- normalized structured rules

We should not treat policy as a single blob of text.

### Canonical rule types for MVP

- permitted uses
- maximum height
- minimum height
- FAR / FSI
- lot coverage
- front, rear, and side setbacks
- stepbacks
- angular plane rules where applicable
- lot frontage minima
- lot area minima
- parking ratios
- loading requirements
- amenity space requirements
- open space requirements
- unit or density limits where applicable

### Policy applicability hierarchy

The evaluation engine should support precedence such as:

1. site-specific exceptions
2. overlay zones
3. area-specific plans
4. base zoning
5. higher-level plans and guidance

### Non-negotiable policy outputs

Every resolved rule should be able to point to:

- source document
- section or page reference
- effective date
- jurisdiction
- geometry or geographic applicability
- extraction confidence
- parser version

## Recommended Product Semantics

Every analysis result should explicitly label:

- source facts
- derived rules
- user overrides
- simulation assumptions
- model predictions

Example:

- source fact: a bylaw clause states a 36 m maximum height
- derived rule: `max_height_m = 36`
- user override: scenario requests 42 m
- simulation assumption: envelope generated with 42 m target massing
- model prediction: approval likelihood decreases due to variance magnitude

This separation matters because it prevents the platform from blending legal truth, analyst choices, and probabilistic outputs into one opaque number.

## AI Usage Policy

### Good uses of AI

- extracting clauses from unstructured bylaws
- summarizing staff reports and planning rationales
- semantic search over policies and precedents
- ranking similar precedent cases
- generating draft summaries for analysts

### Bad uses of AI

- final compliance determination
- final geometry calculations
- final financial calculations
- citation replacement

### Operating rule

LLMs may assist the system, but deterministic engines and versioned source data must remain authoritative.

## Technical Architecture

## High-level architecture

Start with a modular monolith or a small set of domain services. Do not start with a large microservice fleet.

At minimum, the system should include:

- API layer
- background job workers
- geospatial database
- object storage
- search index
- orchestration for scheduled and long-running work

### Core service map

| Service | Purpose |
|---|---|
| API Gateway / Edge | Auth, rate limits, idempotency, routing |
| Project Service | Organizations, users, projects, shares, templates |
| Geospatial Service | Parcel resolution, spatial joins, geometry metrics |
| Policy Service | Policy resolution, citations, clause graph, normalized rules |
| Document Service | Raw document storage, OCR text, extraction artifacts |
| Simulation Service | Envelope generation, massing runs, scenario diffing |
| Layout Service | Unit mix and floor-plate scenarios |
| Finance Service | Comparable normalization and financial outputs |
| Precedent Service | Retrieval, similarity, explainable risk scoring |
| Export Service | PDFs, CSVs, spreadsheets, 3D exports |
| Ingestion Orchestrator | Source refresh, parsing, validation, publish snapshots |

## Storage architecture

### Primary data stores

- PostgreSQL + PostGIS for transactional and spatial data
- S3-compatible object storage for raw documents, artifacts, and exports
- Redis for cache, locks, and short-lived coordination
- OpenSearch or Elasticsearch for full-text and document retrieval

### Vector search

For early MVP, `pgvector` is acceptable for precedent and semantic search. For growth, move heavier retrieval workloads into OpenSearch or a dedicated retrieval tier if query volume or corpus size demands it.

### Workflow and scheduling

- Temporal for long-running user-facing workflows is preferred
- Dagster or Airflow for scheduled ingestion and data refresh pipelines is preferred

If we need to move faster initially, Celery can work as a first async layer, but we should treat it as a stepping stone rather than the ideal end state for a workflow-heavy platform.

## Compute and deployment recommendation

### Local development

Use Docker Compose with:

- API service
- worker service
- PostgreSQL + PostGIS
- Redis
- MinIO or local S3-compatible storage
- OpenSearch if used in MVP

### Production recommendation

The best scalable starting point is:

- managed containers on AWS ECS/Fargate or GCP Cloud Run style infrastructure
- managed PostgreSQL
- managed Redis
- managed object storage
- managed search

### Railway position

Railway is acceptable for a quick internal prototype or short-lived demo. It is not my preferred default for a backend with heavy spatial workloads, scheduled ingestion, and long-running analysis jobs if we are optimizing for scalable best practices from the start.

## Recommended tech stack

### Application and orchestration

- TypeScript or Python for the main API layer
- Python for ingestion, parsing, optimization, and ML-adjacent workflows

### Suggested framework split

- FastAPI for API and worker-facing orchestration if we want a Python-first stack
- or NestJS for API plus Python workers if we want stronger separation between serving and compute

### Data and infra

- PostgreSQL 16 + PostGIS
- Redis
- S3-compatible object storage
- OpenSearch
- pgvector for early semantic search
- Terraform for infrastructure as code
- GitHub Actions for CI/CD
- OpenTelemetry for traces and metrics

## Database Design

### Core tables

```sql
-- Tenant and project model
organizations (id, name, created_at)
workspace_members (id, organization_id, user_id, role, created_at)
projects (id, organization_id, name, status, created_at, updated_at)
project_parcels (id, project_id, parcel_id, role, created_at)
project_shares (id, project_id, shared_with_email, permission, created_at)
scenario_runs (id, project_id, parent_scenario_id, scenario_type, input_hash, created_at)

-- Jurisdiction and parcels
jurisdictions (id, name, province, country, bbox_geom, metadata)
parcels (id, jurisdiction_id, pin, address, geom, lot_area, lot_frontage, current_use, assessed_value)
parcel_metrics (id, parcel_id, metric_type, metric_value, unit, computed_at)

-- Policy model
policy_documents (id, jurisdiction_id, doc_type, title, source_url, effective_date, object_key, parse_status)
policy_versions (id, document_id, parser_version, extracted_at, confidence_summary, published_at)
policy_clauses (id, policy_version_id, section_ref, page_ref, raw_text, normalized_type, normalized_json, confidence)
policy_references (id, from_clause_id, to_clause_id, relation_type)
policy_applicability_rules (id, policy_clause_id, jurisdiction_id, geometry_filter, use_filter, applicability_json)

-- Dataset layers
dataset_layers (id, jurisdiction_id, name, source_url, license_status, refresh_frequency, published_at)
dataset_features (id, dataset_layer_id, source_record_id, geom, attributes_json, effective_date)
feature_to_parcel_links (id, feature_id, parcel_id, relationship_type)

-- Precedents
development_applications (id, jurisdiction_id, app_number, address, parcel_id, app_type, status, decision, decision_date)
application_documents (id, application_id, doc_type, object_key, extracted_text, embedding)
rationale_extracts (id, application_document_id, extract_type, content, confidence)

-- Simulation and finance
massings (id, scenario_run_id, template_name, geometry_3d_key, summary_json)
entitlement_results (id, scenario_run_id, result_json, source_snapshot_id)
financial_runs (id, scenario_run_id, assumption_set_id, output_json)
market_comparables (id, jurisdiction_id, comp_type, effective_date, source, attributes_json)

-- Exports and audit
export_jobs (id, project_id, scenario_run_id, export_type, status, object_key, created_at)
audit_events (id, organization_id, actor_id, event_type, entity_type, entity_id, payload_json, created_at)
```

### Modeling notes

- separate raw source files from parsed artifacts
- separate policy clauses from normalized rule outputs
- separate scenarios from projects
- store immutable scenario input hashes
- store citations and source snapshots on every derived output

## Search Model

There are three search systems in this product:

1. Spatial search
2. Policy search
3. Opportunity search

### Spatial search

Examples:

- parcels within an area
- parcels matching frontage or lot area thresholds
- parcels under specific zoning
- parcels near transit or within overlays

### Policy search

Examples:

- all clauses that constrain height for a parcel
- all parking rules for a project type
- all relevant clauses with citations and applicability

### Opportunity search

Examples:

- parcels where current height is below market-optimal form
- parcels with specific FAR potential
- parcels with favorable precedent density
- parcels matching a development thesis

This third mode requires precomputed parcel features and not just naive live SQL filters.

## Key Workflows

### 1. Ingestion workflow

1. Check source feeds and documents for changes.
2. Store raw source files immutably.
3. Parse geometry, text, tables, and metadata.
4. Run extraction and normalization.
5. Validate schema, geometry validity, and confidence thresholds.
6. Route low-confidence outputs for review if needed.
7. Publish a new version snapshot.
8. Update search indexes and cache invalidation.

### 2. Project analysis workflow

1. Resolve parcel or site selection.
2. Determine jurisdiction and applicable overlays.
3. Resolve effective policy stack with citations.
4. Load dataset overlays and parcel metrics.
5. Generate as-of-right envelope.
6. Run scenario massing.
7. Optionally run layout optimization.
8. Optionally run finance and precedent analysis.
9. Save outputs against a versioned scenario snapshot.
10. Export results asynchronously if requested.

### 3. Variance simulation workflow

1. User creates a scenario fork.
2. Requested overrides are attached to the new scenario.
3. Policy engine produces an alternate interpreted rule stack.
4. Simulation reruns against the modified rule set.
5. Entitlement and precedent scoring rerun with new deltas.
6. Result is stored as a sibling scenario, never as a destructive overwrite.

## Algorithmic Approach

### Building envelope generation

```text
Input: parcel_geometry, policy_rules, overlay_constraints
1. Resolve edge types and frontage conditions.
2. Apply required setbacks and buildable area reductions.
3. Apply lot coverage constraints.
4. Compute height and stepback regimes.
5. Apply angular plane or transition constraints where relevant.
6. Generate candidate envelope geometry.
7. Check FAR / FSI constraints and reduce or reshape if exceeded.
8. Output deterministic envelope geometry plus rule-by-rule compliance deltas.
```

### Unit mix optimization

```text
Goal: maximize revenue or another objective function
Subject to:
- total area <= usable floor area
- unit counts >= 0
- parking, accessibility, and policy constraints
- unit mix ratios where required
- dimensional and floor-plate constraints
```

The first MVP can optimize at the area-allocation level before attempting full floor-plan packing.

### Entitlement and precedent scoring

Use a two-layer system:

1. Retrieval layer
   Retrieve nearby and structurally similar precedent applications.

2. Explainable scoring layer
   Score based on features such as:
   - compliance delta
   - variance magnitude
   - precedent density
   - district similarity
   - rationale similarity
   - decision outcomes

LLMs can summarize rationale and highlight likely risk factors, but approval scoring should not be a black box.

## API Design

Prefer REST with async job resources.

### Key resources

```text
POST   /api/v1/projects
GET    /api/v1/projects/{id}
POST   /api/v1/projects/{id}/parcels

GET    /api/v1/parcels/search
GET    /api/v1/parcels/{id}
GET    /api/v1/parcels/{id}/policy-stack

POST   /api/v1/projects/{id}/scenarios
POST   /api/v1/scenarios/{id}/massings
POST   /api/v1/massings/{id}/layout-runs
POST   /api/v1/scenarios/{id}/financial-runs
POST   /api/v1/scenarios/{id}/entitlement-runs
POST   /api/v1/scenarios/{id}/precedent-searches
POST   /api/v1/scenarios/{id}/policy-overrides

GET    /api/v1/policies/search
GET    /api/v1/precedents/search

POST   /api/v1/exports
GET    /api/v1/jobs/{id}
```

### API design rules

- every write endpoint should support idempotency keys
- long-running operations should return `202 Accepted`
- responses should include source snapshot references
- derived outputs should include citations and assumptions
- scenario creation should be explicit rather than hidden inside mutable updates

## Scalability Strategy

### Data partitioning

Partition or shard by:

- jurisdiction
- source type
- effective date
- spatial region or tile where needed

### Caching

Cache:

- parcel summaries
- policy stacks by parcel set and source snapshot
- frequently used overlay queries
- precedent retrieval results
- export artifacts

### Async and worker design

Anything that can take more than roughly one second should be a background job:

- OCR
- policy extraction
- batch parcel feature generation
- heavy massing runs
- layout optimization
- precedent interpretation
- report export

### Reliability controls

- idempotent ingestion jobs
- retry with backoff
- dead-letter handling
- immutable scenario outputs
- rollbackable policy publishes
- workflow state visibility

## Observability And Operations

We should not wait until late phases to add this.

### Must-have telemetry

- request tracing across API and worker paths
- job duration and failure metrics
- parser confidence distributions
- refresh lag by source
- simulation input hashes
- source snapshot IDs used in each analysis

### Recommended tooling

- OpenTelemetry
- Prometheus / Grafana or managed equivalent
- centralized structured logging
- Sentry or equivalent error tracking

## Implementation Plan

### Phase 1 — Foundation and tenant-safe data model

- [ ] Docker Compose development stack
- [ ] PostgreSQL + PostGIS setup
- [ ] object storage setup
- [ ] Redis setup
- [ ] organizations, users, projects, scenarios, audit tables
- [ ] parcel ingestion for Toronto MVP
- [ ] zoning geometry ingestion for Toronto MVP
- [ ] parcel lookup by address, coordinates, and PIN
- [ ] basic parcel-to-zoning and overlay resolution

### Phase 2 — Policy engine and citations

- [ ] raw document ingestion pipeline
- [ ] parsing and OCR pipeline
- [ ] clause segmentation
- [ ] LLM-assisted extraction into canonical rule schema
- [ ] confidence scoring and review workflow
- [ ] policy versioning and publish snapshots
- [ ] effective policy stack resolution API with citations

### Phase 3 — As-of-right simulation

- [ ] deterministic envelope generation
- [ ] support for setbacks, height, lot coverage, FAR/FSI
- [ ] scenario persistence with immutable input hashes
- [ ] geometry artifact generation
- [ ] async analysis jobs and job status endpoints

### Phase 4 — Layout and finance

- [ ] basic unit mix optimizer
- [ ] market comparable ingestion
- [ ] financial assumption sets
- [ ] pro forma engine
- [ ] exportable scenario summaries

### Phase 5 — Precedent and entitlement

- [ ] development application ingestion
- [ ] precedent search index
- [ ] rationale extraction and summarization
- [ ] explainable entitlement scoring
- [ ] variance scenario support

### Phase 6 — Scale and harden

- [ ] managed cloud deployment
- [ ] search tier hardening
- [ ] workflow orchestration hardening
- [ ] caching strategy implementation
- [ ] load testing
- [ ] SSO and stronger org controls
- [ ] compliance, audit, and data retention policies

## Testing And Verification Strategy

### Unit tests

- policy normalization
- policy resolution
- envelope generation
- unit mix optimization
- financial calculations
- entitlement scoring components

### Integration tests

- address to parcel to policy stack
- parcel to envelope
- envelope to unit mix
- unit mix to finance
- scenario fork to variance delta

### Data quality tests

- geometry validity checks
- source completeness checks
- parser schema validation
- citation presence checks
- source snapshot consistency checks

### Accuracy tests

- compare extracted rules against known bylaw samples
- compare envelope outputs against hand-checked zoning scenarios
- evaluate precedent retrieval quality on known applications

### Performance tests

- spatial query concurrency
- background job throughput
- export generation latency
- cache hit effectiveness

## Biggest Risks

### 1. Policy normalization risk

If we cannot reliably transform bylaws into canonical rules, downstream simulation and compliance become brittle.

### 2. Data licensing risk

Private comparable data and some assessment sources may limit storage, modeling, and export rights.

### 3. Explainability risk

Users will reject opaque outputs if they cannot trace results back to source text, assumptions, and scenarios.

### 4. Jurisdiction expansion risk

Toronto is only the MVP. Future cities will vary significantly in source formats and rule semantics.

### 5. Geometry edge-case risk

Irregular lots, missing frontage information, conflicting overlays, and incomplete data can break naive envelope logic.

## What We Should Build First

If the goal is a credible and scalable clone, the first build should prioritize:

1. Toronto parcel and zoning foundation
2. versioned policy ingestion with citations
3. deterministic as-of-right envelope generation
4. scenario storage and exports
5. precedent retrieval
6. financial modeling

That sequencing gives us a trustworthy core before we add higher-variance AI-heavy features.

## Bottom Line

The most important architectural insight is that this is not just a GIS app and not just an LLM app. It is a versioned decision platform that must combine spatial data, policy interpretation, deterministic simulation, and explainable outputs.

If we get provenance, policy normalization, scenario versioning, and async infrastructure right, the system can scale. If we skip those and optimize only for demo speed, we will end up with outputs that look impressive but are difficult to trust, debug, or sell to serious development teams.
