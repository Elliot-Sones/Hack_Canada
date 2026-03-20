# Arterial Clone: Backend, Data, and Infrastructure Analysis

## Scope Note

The public project URL shared for `https://www.arterial.design/project/VmKyLQTbIwb11/overview` appears locked when accessed without an authenticated Arterial session, so this analysis is derived from Arterial's public documentation and product pages. The goal here is to reverse-engineer the backend product shape and turn it into an implementation plan focused on scalable infrastructure and sound engineering practices.

## What We Are Actually Building

Arterial is not just a parcel search tool and not just a zoning reader. It is a land-development decision engine that combines:

- geospatial parcel discovery
- policy ingestion and citation resolution
- dataset overlays from public and private sources
- deterministic geometry and massing simulation
- layout optimization
- financial modeling
- precedent retrieval from development applications
- policy override and variance simulation
- export and collaboration workflows

The backend therefore needs to behave like a combination of:

- GIS platform
- policy knowledge graph
- document processing pipeline
- geometry engine
- financial model service
- search and recommendation engine
- long-running job orchestration system

## Product Jobs To Be Done

The core user jobs appear to be:

1. Find parcels or sites worth analyzing.
2. Pull all relevant policies, zoning, and overlays for the site.
3. Resolve what is allowed as-of-right and what requires variance.
4. Generate a buildable envelope and candidate massings.
5. Turn a massing into unit/layout scenarios.
6. Estimate viability using comparable rents, sales, and construction costs.
7. Check precedent and approval probability using nearby applications.
8. Export the result as a report, spreadsheet, CSV, or 3D package.

## Primary Users

- Development analysts searching for opportunities
- Architects or planners testing form and compliance
- Acquisitions teams screening parcels at scale
- Entitlement consultants reviewing policy risk
- Real estate finance teams testing viability and returns
- Organization admins managing team data, permissions, and templates

## Inputs And Outputs

### User inputs

At minimum, the system needs the following user inputs:

- address or parcel selection
- project boundary, including one or more parcels
- project target parameters such as use, typology, desired storeys, or density target
- manual policy values when jurisdiction data is incomplete or non-digitized
- massing configuration such as setbacks, stepbacks, height, cores, window wells, and template choice
- layout inputs such as unit types, area ranges, dimensional ranges, unit priorities, and amenity constraints
- financial assumptions such as cap rate, expenses, vacancy, absorption, and target tenure
- variance overrides for policy simulation
- precedent search prompts or filters
- export/reporting preferences

### User outputs

The user should receive:

- parcel summary and site geometry
- effective policy stack for the site
- cited rule extracts with source links and versioning
- as-of-right envelope and rule ranges
- candidate massings and geometry metrics
- unit-mix and floor-plate options
- financial projections and comparable sets
- entitlement checks with pass or fail reasoning
- precedent matches with approval outcomes and rationales
- probability of variance success or approval likelihood
- exports such as PDF, CSV, pro forma spreadsheet, and 3D files

## Functional Domains We Need

### 1. Parcel and map domain

Responsibilities:

- address geocoding
- parcel search
- parcel geometry and adjacency
- frontage, area, depth, lot characteristics
- multi-parcel assembly support
- spatial overlays and jurisdiction lookup

Core entities:

- `parcel`
- `parcel_geometry`
- `parcel_assessment`
- `parcel_jurisdiction`
- `project_parcel`

### 2. Policy domain

Responsibilities:

- ingest zoning by-laws, official plans, design guidelines, amendments, and planning bulletins
- version policy documents by jurisdiction and effective date
- extract clauses and cross-references
- map policy clauses to normalized rule types
- resolve applicable rules for a site and project type

Core entities:

- `policy_document`
- `policy_version`
- `policy_clause`
- `policy_reference`
- `policy_applicability_rule`
- `project_policy_override`

### 3. Dataset domain

Responsibilities:

- ingest polygon and point datasets
- store lineage and source metadata
- support dataset filtering and parcel overlays
- expose development applications, permits, designations, demographics, transit, and market signals

Core entities:

- `dataset_layer`
- `dataset_feature`
- `dataset_refresh_job`
- `source_record`
- `feature_to_parcel_link`

### 4. Massing and geometry domain

Responsibilities:

- generate buildable envelopes from parcel geometry and setbacks
- model massing templates and user-customized building form
- compute floor area, GFA, GLA, shadow constraints if needed later, and geometric compliance
- maintain deterministic versions of each simulation

Core entities:

- `massing`
- `massing_template`
- `massing_revision`
- `storey_profile`
- `reserved_space`
- `geometry_metric`

### 5. Layout optimization domain

Responsibilities:

- unit library and regional defaults
- area-based and dimension-based unit simulation
- floor-plate packing/allocation
- equalization and floor-specific locking
- revenue-aware optimization

Core entities:

- `unit_type`
- `unit_mix`
- `floor_plate`
- `layout_run`
- `layout_candidate`

### 6. Entitlement and precedent domain

Responsibilities:

- compare project geometry to policy ranges
- split objective legal checks from softer design-guideline checks
- find comparable applications nearby
- interpret planning rationales and project data sheets
- estimate approval probability

Core entities:

- `entitlement_rule`
- `entitlement_run`
- `entitlement_result`
- `precedent_case`
- `precedent_search`
- `precedent_match`
- `rationale_extract`

### 7. Finance domain

Responsibilities:

- comparable rents and sales
- construction costing
- unit-level and project-level revenue projections
- cap rate, NOI, valuation, and return estimates
- custom assumption overrides

Core entities:

- `market_comparable`
- `construction_cost_model`
- `financial_assumption_set`
- `financial_run`
- `financial_output`

### 8. Export and collaboration domain

Responsibilities:

- PDF reports
- CSV exports
- 3D exports
- organization-scoped templates
- sharing and permissions
- auditable report generation

Core entities:

- `organization`
- `workspace_member`
- `project_share`
- `export_job`
- `report_template`

## Required Data To Build This Well

### Core source-of-truth data

- cadastral parcel geometries
- address and geocoder data
- zoning maps and zoning by-laws
- official plan and secondary plan maps
- urban design guidelines and built-form rules
- permitting and development application datasets
- planning rationale documents, staff reports, and architectural attachments
- parcel assessments and ownership where legally available
- MLS sale and leasing comparables or equivalent licensed feeds
- construction cost references

### Strongly recommended enrichment data

- transit stops and frequency
- amenities and neighborhood services
- demographic and socioeconomic data
- environmental constraints
- floodplain and conservation overlays
- heritage overlays
- school or infrastructure boundaries

### Metadata we must not skip

- source URL
- publisher
- acquisition timestamp
- effective date
- jurisdiction
- geometry CRS/SRID
- parser version
- confidence score
- lineage chain back to original source

## Policy And Data Governance Requirements

This category is just as important as the modeling itself.

### External data policy requirements

- Every dataset and policy source needs explicit licensing status.
- MLS and proprietary market data likely require strict downstream-use rules.
- We need retention and redistribution rules for uploaded planning documents.
- We need source attribution in every user-facing result.

### Internal governance requirements

- Every simulation must be reproducible against a frozen snapshot of inputs and data versions.
- No compliance decision should rely only on LLM output.
- Deterministic rule evaluation must remain the source of truth.
- Low-confidence extractions should enter a review queue before becoming production policy facts.
- Policy refreshes need audit logs and rollback capability.

### Security and privacy requirements

- SSO and role-based access control for organizations
- row-level organization isolation
- encryption at rest and in transit
- signed URLs for private document access
- admin audit trails for exports and sharing
- secrets management through a managed secret store

## Recommended Product Semantics

To make the backend explainable and trustworthy, every result should separate:

- `source facts`
- `derived rule interpretations`
- `simulation assumptions`
- `model predictions`

For example:

- A zoning height limit is a source fact.
- The normalized rule `max_height_m = 36.0` is a derived interpretation.
- A chosen 42 m tower is a simulation assumption.
- A 61 percent variance-success score is a model prediction.

If we keep these layers separate, the system remains explainable and debuggable.

## Architecture Recommendation

## High-level architecture

Use a modular service architecture, but do not start with dozens of microservices. The best path is:

- modular monolith or a small set of domain services for the product API
- event-driven ingestion and long-running jobs
- dedicated geospatial and search infrastructure
- explicit separation between online serving and offline ingestion

### Core services

1. `api-gateway`
   Exposes external REST APIs, auth, rate limits, idempotency, and job submission.

2. `project-service`
   Manages organizations, users, projects, sharing, templates, and user inputs.

3. `geospatial-service`
   Handles parcel lookup, spatial joins, geometry metrics, overlays, and map queries.

4. `policy-service`
   Resolves applicable policies, clause graphs, versioning, and citations.

5. `document-service`
   Stores raw documents, OCR output, clause extractions, and provenance.

6. `simulation-service`
   Generates massings, layout runs, entitlement checks, and variant simulations.

7. `precedent-service`
   Finds similar applications, indexes planning rationales, and returns explanatory matches.

8. `finance-service`
   Computes comparable-driven revenue, valuation, and construction cost outputs.

9. `export-service`
   Generates PDFs, spreadsheets, CSVs, and 3D exports asynchronously.

10. `ingestion-orchestrator`
   Runs scheduled refresh jobs, source sync, parsing, and validation pipelines.

### Storage and infrastructure

- `PostgreSQL + PostGIS`
  Primary transactional store and spatial query engine.

- `S3-compatible object storage`
  Raw source files, OCR artifacts, document pages, generated reports, and 3D exports.

- `OpenSearch or Elasticsearch`
  Full-text search for clauses, documents, and precedent content; optionally vector search too.

- `Redis`
  Caching, distributed locks, and short-lived job coordination.

- `Queue / workflow engine`
  Prefer `Temporal` for user-facing long-running workflows and retry semantics.

- `Batch orchestration`
  Prefer `Dagster` or `Airflow` for scheduled ingestion across jurisdictions.

- `Data warehouse`
  `ClickHouse`, `BigQuery`, or `Snowflake` for usage analytics and large-scale benchmarking.

### Compute

Recommended default:

- containerized services
- managed Kubernetes if the team already knows it
- otherwise ECS/Fargate or Cloud Run-style managed containers for lower ops load

My practical recommendation:

- start on ECS/Fargate or Cloud Run style infrastructure for API and workers
- use managed Postgres
- use managed OpenSearch
- move heavy simulation workers to autoscaled worker pools
- only move to full Kubernetes when scale or platform constraints justify it

## Data Flow Design

### A. Ingestion flow

1. Scheduled sync checks source endpoints or files.
2. Raw artifacts are stored in object storage unchanged.
3. Parsing extracts geometry, tables, clauses, references, and metadata.
4. Validation checks schema, geometry validity, completeness, and confidence.
5. Normalization maps records into canonical entities.
6. Search indexes are updated.
7. A new version snapshot is published for online serving.

### B. Project analysis flow

1. User selects parcel or address.
2. Geospatial service resolves parcel set and jurisdiction.
3. Policy service resolves applicable policy stack.
4. Dataset service loads overlays and source facts.
5. Simulation service generates buildable envelope and candidate massing.
6. Layout service generates floor-plate scenarios.
7. Finance service produces viability outputs.
8. Entitlement and precedent services evaluate compliance and approval likelihood.
9. Export service materializes outputs for sharing.

### C. Variance simulation flow

1. User selects policies to override.
2. System forks the project context into a variant scenario.
3. Policy-service produces an alternate rule stack.
4. Simulation and finance rerun against the variant.
5. Precedent-service re-ranks supporting cases.
6. Results are stored as a comparable scenario, not as a destructive overwrite.

## How To Model Policies Correctly

This is the hardest part of the product.

Do not store policy information only as text blobs. The backend needs both:

- raw legislative text
- normalized structured rules

### Canonical rule types

At minimum, normalize these policy classes:

- permitted uses
- maximum height
- minimum height
- FSI/FAR
- lot coverage
- setbacks by edge type
- stepbacks by floor range
- angular plane or transition rules
- frontage and lot size minima
- parking requirements
- loading requirements
- amenity space requirements
- open space or landscaping requirements
- tower separation or distance constraints
- density/unit count caps

### Policy graph requirements

Each clause should be able to point to:

- source document page/section
- references to other clauses
- applicability conditions
- jurisdiction and geography
- effective date range
- confidence of extraction
- normalized output fields

This graph is what makes "find the full set of regulations faster than any human could" technically possible.

## Where AI Should And Should Not Be Used

### Good uses of AI

- extracting clauses from messy PDFs
- summarizing planning rationales
- helping users search policy text in natural language
- generating candidate massing templates
- ranking likely precedents

### Bad uses of AI

- final legal compliance decisions
- final geometric calculations
- final financial calculations
- replacing citation chains

Use LLMs as assistants around deterministic engines, not as the authoritative engine.

## Simulation And Geometry Engine Design

### Deterministic geometry kernel

Use a deterministic geometry pipeline with explicit revisioning. Inputs should include:

- parcel polygon
- setback lines
- building typology parameters
- reserved spaces
- floor plate constraints
- selected unit library

Outputs should include:

- 2D envelopes
- 3D massing geometry
- GFA and GLA
- efficiency ratios
- unit counts
- compliance deltas by rule

### Why this matters

If users change a single setback, floor plate rule, or amenity size, they need a reproducible diff. That means every simulation result should be immutable and hashable.

## Precedent And Approval Probability Engine

This is the second hardest part after policy normalization.

### Data required

- application metadata
- location and radius indexing
- approval or rejection outcomes
- staff reports
- planning rationale extracts
- submitted plans and data sheets
- linked clauses/policy references
- project form descriptors such as height, density, use, setbacks, and built form

### Modeling approach

Use a two-layer approach:

1. Retrieval layer
   Find nearby and structurally similar cases using spatial, textual, and form-based similarity.

2. Scoring layer
   Produce an approval-likelihood score using explainable features such as compliance delta, district similarity, precedent density, and rationale pattern similarity.

Do not start with a black-box ML model as the only answer. Start with interpretable scoring and add statistical models once labeled data quality is strong.

## Financial Modeling Design

### Inputs

- unit mix
- projected lease or sale mode
- comp set
- construction type
- hard and soft costs
- cap rate
- vacancy
- operating expenses
- financing assumptions

### Outputs

- projected rent or sales per unit type
- total revenue
- NOI
- valuation
- total construction cost
- residual land value
- simple return metrics

### Important constraint

Financial outputs should clearly distinguish:

- market-derived values
- user overrides
- modeled assumptions

This is important for trust and for enterprise adoption.

## Search And Query Model

There are really three search systems in the product:

1. Spatial search
   Parcel, radius, overlay, adjacency, and jurisdiction search.

2. Policy search
   Clause and citation retrieval with structured filters.

3. Opportunity search
   Reverse search for parcels that match a development thesis.

That third category is not trivial. It means the system must support precomputed parcel features and fast filtering across:

- geometry metrics
- zoning potential
- precedent density
- market scores
- template compatibility
- HBU scores

## Scalability Considerations

### Partitioning strategy

Partition major datasets by:

- jurisdiction
- source type
- effective date/version
- geometry tile or spatial region when necessary

### Caching strategy

Cache:

- parcel summaries
- policy stacks by parcel set and version
- dataset overlay tiles
- comparable result sets
- precedent searches
- export artifacts

### Async job strategy

Anything that can take more than a second should be asynchronous:

- OCR and document extraction
- major policy refreshes
- massing generation beyond small cases
- layout optimization
- entitlement batch runs
- precedent interpretation
- PDF and pro forma generation

### Reliability strategy

- idempotent ingestion jobs
- dead-letter queues
- automatic retry with backoff
- immutable simulation revisions
- schema versioning
- rollbackable policy snapshots

## Best-Practice API Design

Prefer external REST APIs with async job resources and webhook support.

Example API resources:

- `POST /projects`
- `POST /projects/{id}/parcels`
- `POST /projects/{id}/policy-overrides`
- `POST /projects/{id}/massings`
- `POST /massings/{id}/layout-runs`
- `POST /massings/{id}/entitlement-runs`
- `POST /projects/{id}/precedent-searches`
- `POST /projects/{id}/financial-runs`
- `POST /exports`
- `GET /jobs/{id}`

Important design choices:

- every write endpoint should support idempotency keys
- long-running work returns `202 Accepted`
- responses should include source-version references
- every derived result should include citations and assumptions

## Observability And Operations

This system will be impossible to trust without strong observability.

Must-have telemetry:

- trace every analysis request across services
- log source versions used in every simulation
- emit metrics for parser confidence, refresh lag, job duration, and failure rates
- record explainability metadata for approval scoring
- store simulation input hashes for reproducibility

Recommended tooling:

- OpenTelemetry
- Prometheus/Grafana or managed equivalent
- centralized structured logs
- Sentry or equivalent exception tracking

## Recommended Tech Stack

This is a pragmatic stack, not the only possible one.

### Application layer

- `TypeScript` for API and orchestration
- `Python` for data ingestion, document extraction, ML, and optimization workloads

### Serving

- `FastAPI` or `NestJS` for APIs
- `gRPC` only for internal high-throughput service boundaries if needed later

### Data

- `PostgreSQL + PostGIS`
- `OpenSearch`
- `Redis`
- `S3`
- `pgvector` or OpenSearch vector search for rationale and document retrieval

### Jobs

- `Temporal`
- `Dagster` or `Airflow`

### Infra

- managed container platform
- managed Postgres
- managed search
- IaC with `Terraform`
- CI/CD with GitHub Actions or equivalent

## Recommended Delivery Phases

### Phase 1: Strong MVP

Build only:

- organization, auth, and projects
- parcel search and parcel geometry
- one pilot jurisdiction
- policy ingestion for zoning and official plan
- deterministic policy resolution with citations
- basic massing envelope generation
- simple PDF and CSV export

Do not build yet:

- full precedent scoring
- AI HBU generation
- advanced layout optimization
- construction-cost modeling depth

### Phase 2: Decision engine

Add:

- layout optimization
- market comparables
- financial analysis
- entitlement checks
- precedent retrieval

### Phase 3: Competitive differentiation

Add:

- approval probability models
- variance simulation
- reverse parcel search
- organization templates
- multi-jurisdiction support

### Phase 4: Enterprise hardening

Add:

- SSO/SAML
- granular permissions
- dataset marketplace or custom source onboarding
- tenant-specific models and templates
- SLA-backed refresh pipelines

## Biggest Risks

### 1. Policy normalization

If policies are not transformed into a reliable canonical rule model, everything downstream becomes brittle.

### 2. Source licensing

MLS and some city datasets may constrain reuse, storage, and export.

### 3. Explainability

Users in this domain will not trust opaque outputs. Every conclusion needs citations and assumptions.

### 4. Jurisdiction variance

Rules differ dramatically across cities. A city-by-city abstraction strategy is necessary.

### 5. Geometry edge cases

Irregular parcels, easements, missing setbacks, and partial data will produce hard simulation failures if not modeled carefully.

## What I Would Build First If We Were Starting Today

If the goal is a credible and scalable clone, I would start with:

1. one city
2. parcel plus policy plus citation engine
3. deterministic as-of-right envelope generation
4. basic project scenarios and exports
5. precedent retrieval second
6. financial modeling third

That ordering gives us a trustworthy foundation before we layer on AI-heavy features.

## Bottom Line

The true core of the product is not the UI. It is the combination of:

- a jurisdiction-aware geospatial platform
- a versioned policy graph
- a deterministic geometry and simulation engine
- a precedent retrieval and interpretation layer
- a comparable-driven finance layer

If we build those pieces with strong versioning, explainability, and async job infrastructure, we can recreate the product in a way that scales. If we skip data lineage, policy normalization, or reproducible simulations, the platform will look good in demos but fail in real land-development workflows.

## Public Sources Used

- https://www.arterial.design/project/VmKyLQTbIwb11/overview
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
