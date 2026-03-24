# CoCivil — AI-Powered Civil Development Platform

> **Auto-maintained**: Updated after every file edit/creation. See `.claude/CLAUDE.md` for rules.
> **Last updated**: 2026-03-21 (login page: scroll fix, session exchange fix, Google sign-in; Celery worker; parcel performance; sidebar grouping) | **PRD**: [`.claude/docs/PRD.md`](.claude/docs/PRD.md)

---

## Product Description

**CoCivil** is an AI-powered due-diligence and design platform for land development in Ontario, Canada. It turns a plain-English development query into a complete planning submission package — compliance matrices, planning rationales, precedent reports, massing models, floor plans, and infrastructure designs — in minutes instead of weeks.

### What It Does

- **Parcel Intelligence** — Search any Toronto address. Instantly retrieve zoning (By-law 569-2013), Official Plan designation, overlays, setbacks, height limits, and lot coverage from live Toronto Open Data.
- **AI Planning Assistant** — Chat with an AI agent grounded in Ontario planning law (Planning Act, PPS 2024, O.Reg 462/24, Bills 23/185/60). It answers zoning questions, proposes variance strategies, and identifies approval pathways.
- **Automated Document Generation** — Generate planning rationales, compliance reports, shadow studies, and submission packages. Every document is grounded in cited policy and flagged for professional review.
- **3D Massing & Floor Plans** — Describe a building in plain English; CoCivil generates a 3D massing model (Three.js) and editable floor plans (Konva.js) with real-time OBC compliance checking.
- **Infrastructure Design** — Upload pipeline DXFs or describe infrastructure; get 3D pipe network visualization, OPSD-compliant specs, and condition assessments.
- **Precedent Research** — AI-powered search of Committee of Adjustment, Ontario Land Tribunal, and CanLII decisions for comparable approvals/refusals near the site.
- **Policy RAG Engine** — Fine-tuned retrieval-augmented generation over Ontario planning documents, zoning by-laws, and building code references via ChromaDB vector search.

### Who It's For

- Land developers evaluating site feasibility
- Urban planners preparing submission packages
- Architects exploring massing and floor plan options
- Civil engineers designing infrastructure networks
- Municipal staff reviewing applications

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (Next.js 16 App Router + Better Auth)          │
│  MapLibre GL · Three.js · Konva.js                       │
├─────────────────────────────────────────────────────────┤
│  Backend (FastAPI + SQLAlchemy async)                    │
│  21 API routers · 105 endpoints · 41 services · 10 tasks  │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL + PostGIS    │  ChromaDB (RAG vectors)      │
│  Toronto Open Data CKAN  │  Claude / OpenAI LLM         │
└─────────────────────────────────────────────────────────┘
```

| Layer | Tech |
|-------|------|
| Frontend | Next.js 16, App Router, Better Auth, MapLibre GL, Three.js, Konva.js |
| Backend | FastAPI, SQLAlchemy 2.0 (async), Pydantic 2.7+, Structlog |
| Database | PostgreSQL + PostGIS, GeoAlchemy2, Alembic migrations |
| AI | Claude (primary), OpenAI (fallback), ChromaDB RAG |
| Task Queue | Celery 5.3+ with Redis broker |
| Deploy | Docker, Railway, AWS S3 |

---

## Table of Contents

1. [Backend — `app/`](#backend--app)
2. [Frontend — `frontend/`](#frontend--frontend-nextjs-16-app-router)
3. [Fine-Tuned RAG — `fine-tuned-RAG/`](#fine-tuned-rag--fine-tuned-rag)
4. [Knowledge — `knowledge/`](#knowledge--knowledge)
5. [Scripts — `scripts/`](#scripts--scripts)
6. [Tests — `tests/`](#tests--tests)
7. [Data & Infrastructure Files](#data--infrastructure-files)
8. [Config & DevOps](#config--devops)
9. [API Endpoint Reference](#api-endpoint-reference)

---

## Backend — `app/`

### Entry Points

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app factory, lifespan (Redis pool warmup), route registration, middleware |
| `app/config.py` | Settings (DB, AI provider, S3, Auth0) via Pydantic BaseSettings |
| `app/database.py` | SQLAlchemy dual async/sync engines & session factories |
| `app/dependencies.py` | FastAPI dependency injection (JWT auth, multi-tenant org scoping) |
| `app/devtools.py` | Preflight connectivity checks (DB, Redis, S3, Docker) |
| `app/celery_app.py` | Celery application config (broker=Redis, JSON serialization, 9 task modules) |

### HTTP Clients (`app/clients/`)

| File | Purpose |
|------|---------|
| `arcgis_rest.py` | Generic ArcGIS REST FeatureServer client (pagination via objectIds, metadata, retry with exponential backoff) |

### Middleware (`app/middleware/`)

| File | Purpose |
|------|---------|
| `request_id.py` | Assigns/propagates X-Request-ID header per request |
| `idempotency.py` | Redis-backed idempotency key enforcement (24h TTL) |

### Database Models (`app/models/`)

| File | Purpose |
|------|---------|
| `base.py` | Base model (UUIDPrimaryKey, TimestampMixin, GovernanceMixin) |
| `plan.py` | Development plan |
| `geospatial.py` | Parcel, zoning, overlay |
| `entitlement.py` | Variances, approvals |
| `infrastructure.py` | PipelineAsset (water, sewer, gas), ElectricalAsset (power lines, substations), BridgeAsset |
| `finance.py` | Development cost models |
| `policy.py` | Policy references & citations |
| `ingestion.py` | Data ingestion tracking |
| `upload.py` | File upload records (with optional project_id FK) |
| `export.py` | Document export records |
| `dataset.py` | Dataset catalog |
| `facts.py` | Materialized parcel fact tables (ParcelCurrentFact, ParcelBuildingFact, ParcelConstraintFact w/ esa_flag, ParcelZoningFact) + parser traceability (ParserVersion, ParseRun) |
| `design_version.py` | Design version tracking |
| `simulation.py` | Scenario simulation |
| `tenant.py` | Multi-tenant isolation (Project, ProjectNote, ProjectConversation, map_state) |
| `better_auth.py` | Read-only Better Auth session/user models (separate base, excluded from Alembic) |
| `users_db.py` | Billing/auth database models (User, Organisation, Subscription, SubscriptionPlan, TokenAccount, TokenLedger, Invoice, BillingRateCard); two-bucket token design |
| `better_auth.py` | Read-only SQLAlchemy models for Better Auth tables (user, session) on separate DeclarativeBase to stay out of Alembic |

### API Routes (`app/routers/`)

| File | Endpoint | Purpose |
|------|----------|---------|
| `plans.py` | `/api/v1/plans` | Plan CRUD + generation; org_id filter includes NULL (anonymous plans visible to authed users) |
| `parcels.py` | `/api/v1/parcels` | Parcel data & search |
| `entitlement.py` | `/api/v1/entitlements` | Zoning approvals |
| `compliance.py` | `/api/v1/compliance` | OBC interior compliance checks |
| `infrastructure.py` | `/api/v1/infrastructure` | Pipelines, watermains, sewers, electrical — all from typed DB tables |
| `finance.py` | `/api/v1/finance` | Pro formas, cost estimates |
| `assistant.py` | `/api/v1/assistant` | AI chat — single-call with live zoning, electrical, water, and RAG context |
| `exports.py` | `/api/v1/exports` | PDF/Docx generation |
| `ingestion.py` | `/api/v1/ingestion` | CKAN/GeoJSON/ArcGIS import + fact population |
| `uploads.py` | `/api/v1/uploads` | File upload handling |
| `auth.py` | `/api/v1/auth` | Authentication (login, register, session-exchange for Better Auth bridge) |
| `jobs.py` | `/api/v1/jobs` | Async task tracking |
| `projects.py` | `/api/v1/projects` | Project CRUD + notes, conversations, plans, uploads, map state (workspace) |
| `scenarios.py` | `/api/v1/scenarios` | Scenario modeling |
| `simulation.py` | `/api/v1/simulation` | Run simulations |
| `design_versions.py` | `/api/v1/design-versions` | Version control |
| `governance.py` | `/api/v1/governance` | Permissions |
| `policy.py` | `/api/v1/policy` | Policy data |
| `billing.py` | `/api/v1/billing` | Stripe subscriptions, token purchase/consume, invoices, portal |
| `billing_webhooks.py` | `/api/v1/webhooks` | Stripe webhook handler (subscription.updated, invoice.paid, payment_intent events) |
| `health.py` | `/api/health` | Health check |

### Services (`app/services/`)

| File | Purpose |
|------|---------|
| `compliance_engine.py` | Deterministic zoning compliance (no AI) |
| `interior_compliance.py` | OBC interior code checking |
| `infrastructure_compliance.py` | Infrastructure standard compliance |
| `zoning_service.py` | Zoning analysis orchestrator (deterministic) |
| `zoning_parser.py` | By-law 569-2013 zone string parser (regex-based) |
| `policy_stack.py` | RAG-backed policy retrieval (ChromaDB) |
| `geospatial_ingestion.py` | GeoJSON import |
| `ckan_ingestion.py` | Toronto Open Data CKAN integration |
| `arcgis_ingestion.py` | Toronto ArcGIS FeatureServer ingestion (parcels, addresses, buildings, zoning, constraints) |
| `fact_population.py` | Fact table population scripts (SQL UPSERTs from normalized → fact tables) |
| `geospatial.py` | PostGIS spatial operations |
| `overlay_service.py` | Zoning overlay analysis |
| `dxf_parser.py` | Building floor plan DXF parsing |
| `pipeline_dxf_parser.py` | Pipeline network DXF parsing |
| `document_analyzer.py` | AI document understanding |
| `document_processor.py` | Text extraction |
| `thin_slice_runtime.py` | Fast feasibility checks |
| `simulation_runtime.py` | Simulation execution |
| `contractor_trades.py` | Contractor specialty matching |
| `precedent.py` | Planning precedent scoring |
| `benchmarks.py` | Development benchmarks |
| `design_version_service.py` | Design version management |
| `governance.py` | Role/permission management |
| `access_control.py` | Fine-grained access control |
| `job_service.py` | Unified job status lookup across 7 async tables |
| `storage.py` | File storage (S3/MinIO via boto3) |
| `validation.py` | Data validation for source metadata, policy, precedent, finance |
| `reference_data.py` | DB-backed reference data management (templates, unit types) |
| `idempotency.py` | Pydantic-aware wrapper over Redis idempotency cache |
| `infrastructure_ingestion.py` | CKAN ingestion for sewers, bridges |
| `water_main_ingestion.py` | Ingests Toronto distribution water mains from GeoJSON into pipeline_assets |
| `electrical_capacity.py` | Deterministic electrical demand analysis (CEC Rule 8-200 tables + grid scoring) |
| `electrical_ingestion.py` | Ingests power lines & substations from Overpass API into electrical_assets |
| `cache.py` | Redis cache-aside helper (`get_or_fetch`) for high-traffic parcel endpoints (silent fallthrough on failure) |
| `token_service.py` | Token grant/consume/renew/top-up; two-bucket rules (subscription first, spill to purchased) |
| `submission/templates.py` | Document templates & AI prompts; includes Municipal Servicing section in planning_rationale and due_diligence_report |
| `submission/context_builder.py` | Submission context assembly; accepts infrastructure param, builds servicing_summary/water_servicing/sewer_servicing/electrical_servicing keys |
| `submission/generator.py` | AI-driven document generation |
| `submission/review.py` | Submission review & QA |
| `submission/readiness.py` | Readiness checks |
| `submission/citation_verifier.py` | Citation validation |
| `submission/document_selector.py` | Document selection logic; intent-first mode generates only user-requested doc types |

### Data & Policy (`app/data/`)

| File | Purpose |
|------|---------|
| `toronto_zoning.py` | By-law 569-2013 standards (hardcoded) |
| `ontario_policy.py` | Policy hierarchy, PPS 2024, OP designations, legislation |
| `toronto_policy_seed.py` | Toronto-specific policy seed data |
| `civil_standards.py` | Civil infrastructure standards |
| `infrastructure_policy.py` | Infrastructure policy rules |
| `obc_interior_standards.py` | Ontario Building Code interior standards |
| `electrical_standards.py` | CEC demand tables, Toronto Hydro service ratings, voltage tiers (OESC CSA C22.1) |

### Schemas (`app/schemas/`)

| File | Purpose |
|------|---------|
| `common.py` | HealthResponse, JobAccepted, PaginationParams, Citation |
| `plan.py` | PlanGenerateRequest, PlanResponse, SubmissionDocumentResponse, readiness |
| `entitlement.py` | EntitlementRunRequest/Response, PrecedentSearchRequest/Response |
| `geospatial.py` | ParcelSearchParams, ParcelResponse, PolicyStackResponse, ZoningAnalysisResponse |
| `assistant.py` | AssistantChatRequest/Response (+ parcel_id, lat, lng fields), ModelParseRequest, InfraModelParseRequest |
| `finance.py` | FinancialRunRequest/Response, FinancialAssumptionSetReferenceResponse |
| `infrastructure.py` | PipelineComplianceRequest, BridgeComplianceRequest, NearbyPipelineRequest |
| `simulation.py` | MassingRequest/Response, LayoutRunRequest/Response, UnitTypeReferenceResponse |
| `tenant.py` | ProjectCreate/Update/Response (with counts), NoteCreate/Update/Response, ConversationCreate/Update/Response/Summary, MapStateUpdate, ScenarioCreate/Response, AddParcelRequest |
| `job.py` | JobStatusResponse (unified across all async job types) |
| `auth.py` | RegisterRequest, LoginRequest, TokenResponse, SessionExchangeRequest |
| `upload.py` | UploadResponse, UploadDetail, GenerateResponseRequest |
| `export.py` | ExportRequest/Response |
| `governance.py` | SnapshotManifestResponse, ReviewQueueItemResponse |
| `design_version.py` | BranchCreate/Response, CommitRequest, VersionResponse |
| `policy.py` | PolicySearchParams, PolicyClauseResponse |

### Background Tasks (`app/tasks/`) — Celery tasks

| File | Purpose |
|------|---------|
| `plan.py` | Main plan generation pipeline; fetches nearby infrastructure and passes to document context |
| `ingestion.py` | CKAN/GeoJSON import |
| `arcgis_ingestion.py` | ArcGIS ingestion tasks (4 phases + full pipeline) |
| `entitlement.py` | Entitlement analysis |
| `infrastructure_ingestion.py` | Infrastructure data import |
| `massing.py` | 3D massing generation |
| `layout.py` | Layout optimization |
| `finance.py` | Financial modeling |
| `export.py` | Document export |
| `document_analysis.py` | Document parsing |

### AI Provider (`app/ai/`)

| File | Purpose |
|------|---------|
| `base.py` | Abstract AI provider interface |
| `claude_provider.py` | Anthropic Claude integration |
| `openai_provider.py` | OpenAI fallback |
| `query_parser.py` | Intent detection & query parsing (extracts requested_documents for selective doc generation) |
| `factory.py` | Provider factory |

---

## Frontend — `frontend/` (Next.js 16 App Router)

### Entry & Config

| File | Purpose |
|------|---------|
| `src/app/layout.tsx` | Root layout (global CSS, Providers wrapper) |
| `src/app/page.tsx` | Landing page route (public) |
| `src/app/Providers.jsx` | Client providers wrapper |
| `src/app/login/page.jsx` | Login/signup page (Better Auth + session exchange) |
| `src/app/dashboard/layout.tsx` | Auth gate (redirects to /login if no session) |
| `src/app/dashboard/page.tsx` | Dashboard route (reads ?address= query param) |
| `src/app/dashboard/[parcelId]/page.tsx` | Dashboard with parcel from URL |
| `src/app/api/auth/exchange/route.ts` | Server-side session exchange (reads BA cookie, calls FastAPI, returns JWT) |
| `src/app/api.js` | API client (all backend calls, session exchange, 401 auto-retry, bbox parcel search, infrastructure, project workspace CRUD — notes, conversations, uploads, map state) |
| `src/app/lib/auth-client.js` | Better Auth client (session management) |
| `src/app/styles/` | Global CSS, landing, ModelViewer, InfrastructureViewer, UserBubble, map-search (selection chips, parcel hover popup), panel (comparison grid, project workspace) styles; variables.css holds tightened Linear-density typography tokens, easing tokens, status colors; spacing.css provides 4px-grid utility classes |
| `src/app/lib/parcelState.js` | Parcel selection state helpers (create, add, remove, toggle, multi-select max 4) |
| `src/app/lib/parcelState.test.js` | Unit tests for parcel selection helpers |
| `next.config.ts` | Next.js config (standalone output, API proxy rewrites) |
| `Dockerfile` | Standalone Next.js Docker build |

### Components (`src/app/components/`)

| File | Purpose |
|------|---------|
| `DashboardView.jsx` | Main dashboard shell (map, sidebar, panels, models); infraOverlayLayers Set for map overlay control; activeProjectId state + floating save indicator showing what artifacts are persisted to the project |
| `LandingPage.jsx` | Home page with Carto dark map bg, SVG brand icon, nav center links, hero typewriter, product demo mockup, How It Works, feature cards, story/vision, final CTA, enhanced footer |
| `MapView.jsx` | Interactive parcel/zoning map (MapLibre GL) with bbox parcel layer, hover/click selection, feature-state highlights, overlay-controlled infrastructure layers (watermains/sewers/electrical) |
| `SelectionChips.jsx` | Floating chip bar for multi-parcel selection (max 4), primary indicator, clear all |
| `SearchBar.jsx` | Address/parcel search |
| `Sidebar.jsx` | Navigation & context panel (building nav + Projects tab) |
| `ChatContextHeader.jsx` | Compact single-line context strip in chat panel showing selected parcels (zone badge + address), uploads, and plan status |
| `ChatPanel.jsx` | AI assistant chat with plan generation, file uploads, contractor matching, polling, multi-parcel context, comparison report generation, chat history persistence (localStorage + project backend), New Chat / History buttons; auto-saves conversations and plans to active project |
| `ProjectsPanel.jsx` | Projects workspace panel (list, create, detail views with tabs: overview, parcels, plans, files, notes, chat); notifies parent on project open/close for save indicator |
| `PolicyPanel.jsx` | Policy extracts, overlays, datasets, uploads, zoning analysis, multi-parcel ComparisonTab, ProjectsPanel routing; OverviewTab integrates useNearbyInfrastructure hook and ServicingSummaryCard |
| `DocumentViewer.jsx` | Markdown document viewer (ReactMarkdown + remark-gfm) |
| `DocumentGallery.jsx` | Document library UI |
| `ModelViewer.jsx` | 3D building massing viewer (Three.js) |
| `FloorPlanView.jsx` | 2D floor plan view (Konva.js) |
| `InfrastructureViewer.jsx` | 3D pipeline network viewer |
| `ElectricalViewer.jsx` | Electrical grid visualization (power lines, substations, voltage tiers) |
| `ContractorCards.jsx` | Contractor/trade recommendation cards |
| `BlueprintOverlay.jsx` | Blueprint display overlay |
| `InfrastructureLayerControl.jsx` | Floating layer toggle panel for DB-backed infrastructure overlays (Water Mains, Sewers, Electrical Grid) |
| `ServicingSummaryCard.jsx` | Municipal servicing summary card with status indicators and capacity check form |
| `UserBubble.jsx` | User profile menu |

### Floor Plan Editor (`src/components/floorplan/`)

| File | Purpose |
|------|---------|
| `FloorPlanEditor.jsx` | Main floor plan canvas (orchestrates layers + panels) |
| **layers/** | |
| `WallLayer.jsx` | Wall rendering & editing |
| `RoomLayer.jsx` | Room zones |
| `DimensionLayer.jsx` | Dimension annotations |
| `OpeningLayer.jsx` | Door/window openings |
| `ComplianceBadgeLayer.jsx` | OBC compliance violation badges |
| **panels/** | |
| `EditorToolbar.jsx` | Tool selection, undo/redo |
| `WallProperties.jsx` | Wall parameter panel |
| `CompliancePanel.jsx` | Code violation list |
| `RoomTypeSelector.jsx` | Room type catalog |
| `DragDropCatalog.jsx` | Component palette |
| `ScaleCalibration.jsx` | Scale/unit setup |

### Infrastructure Viewer (`src/components/infrastructure/`)

| File | Purpose |
|------|---------|
| `PipeNetworkEditor.jsx` | Pipe network editing (Konva) |
| `InfrastructureLayerControl.jsx` | Layer toggles |
| `InfrastructureCatalog.jsx` | Pipe catalog |
| `InfrastructureCompliancePanel.jsx` | Infrastructure compliance checks |
| `PipeProperties.jsx` | Pipe parameter editor |
| `ProfileView.jsx` | Elevation profile view |

### Hooks (`src/hooks/` and `src/app/hooks/`)

| File | Purpose |
|------|---------|
| `useResizable.js` | Resizable panel hook |
| `src/app/hooks/useNearbyInfrastructure.js` | React hook to fetch nearby water, sewer, storm, electrical infrastructure for a parcel |

### Utilities (`src/lib/` and `src/app/lib/`)

| File | Purpose |
|------|---------|
| `src/app/lib/geoUtils.js` | Centroid extraction utility for GeoJSON geometries |
| `buildingGeometry.js` | 3D building geometry helpers |
| `wallGeometry.js` | Wall geometry calculations |
| `floorPlanHelpers.js` | Floor plan utilities |
| `infrastructureGeometry.js` | Pipeline geometry math |
| `parcelState.js` | Parcel data state management, multi-selection helpers (add/remove/toggle, max 4) |
| `chatHistory.js` | localStorage conversation persistence (CRUD, auto-prune at 50, title from first user message) |
| `chatCommands.js` | Chat command parsing |
| `watermainStandards.js` | Water main diameter/depth rules |
| `chatCommands.test.js` | Tests for chat command parsing |
| `parcelState.test.js` | Tests for parcel state functions and multi-selection helpers |

### Dev Harness (`src/dev/`)

| File | Purpose |
|------|---------|
| `ModelViewerHarness.jsx` | Isolated 3D viewer testing (loaded via `?viewerHarness=1`) |
| `modelViewerHarnessData.js` | Sample parcel, model params, floor plans for harness |

---

## Fine-Tuned RAG — `fine-tuned-RAG/`

| File | Purpose |
|------|---------|
| `config.py` | RAG configuration (embedding model, ChromaDB settings) |
| `retriever.py` | Vector search & context retrieval |
| `rag_chain.py` | RAG pipeline (query → retrieval → LLM) |
| `api.py` | FastAPI endpoints for RAG service |
| `ingest.py` | Load documents into ChromaDB |
| `fast_ingest.py` | Optimized bulk ingestion |
| `populate_rag.py` | Parallel population via API (ThreadPoolExecutor) |
| `populate_direct.py` | Direct in-process population (targeted subtopics) |
| `get_context.py` | CLI debug tool — retrieve and print context for a query |
| `run_batch.py` | Batch inspection of retriever results |
| `test_ask.py` | Smoke test — single hardcoded question |
| `check_empty.py` | Audit — count entries missing output |
| `fix_one.py` | One-shot repair for a single entry |
| `chroma_db/` | ChromaDB vector database storage |

---

## Knowledge — `knowledge/`

Domain knowledge for CoCivil's AI systems. Single source directory for RAG ingestion into ChromaDB.

### Research Pipeline (`knowledge/research-pipeline/`)

9 sequential AI research skills for Ontario site-feasibility:

| Skill | Output | Purpose |
|-------|--------|---------|
| `source-discovery` | `source_bundle.json` | Find official data source URLs |
| `parcel-zoning-research` | `normalized_data.json` | Extract zone code, OP designation, overlays |
| `buildability-analysis` | `analysis_packet.json` | Feasibility verdict + compliance gaps |
| `precedent-research` | `precedent_packet.json` | Comparable CoA/ZBA/OLT decisions |
| `constraints-red-flags` | `constraints_packet.json` | OBC hard constraints, risk flags |
| `approval-pathway` | `approval_pathway.json` | Route classification + timeline |
| `report-generator` | `final_report.md` | Client-facing report |
| `infrastructure-assessment` | `condition_assessment.json` | Asset condition rating & rehab priority |
| `infrastructure-standards` | — | OPSD/CSA/MTO standard lookups |

### Document Templates (`knowledge/document-templates/`)

29 ontario-* planning document generation skills (planning rationale, compliance matrix, cover letter, precedent report, etc.).

### Water Policy (`knowledge/water-policy/`)

13 markdown docs + PDF references on Ontario water/sewer regulations, MECP procedures, MTU zone maps.

### Research (`knowledge/research/`)

| File | Purpose |
|------|---------|
| `arterial_backend_clone_analysis.md` | Reverse-engineering analysis of Arterial.design |
| `DATA_PLAN.md` | MVP data plan: 4 dataset tiers, 9-stage ingestion pipeline |
| `DATA_RESEARCH_TEAM_PLAN.md` | 6 parallel research tracks for Toronto MVP |
| `IMPLEMENTATION_PLAN.md` | Full technical spec: schema DDL, algorithms, phase breakdown |
| `SUBMISSION_RESEARCH.md` | Toronto application requirements, document types, policy framework |
| `RAG_LEGAL_DOCUMENT_GENERATION_RESEARCH.md` | RAG architecture research |
| `TRACK_3_4_RESEARCH.md` | Research for Policy Text + Hard Constraint Overlays tracks |
| `TRACK_5_6_RESEARCH.md` | Research for Simulation Defaults + Precedent/Permit tracks |

---

## Scripts — `scripts/`

| File | Purpose |
|------|---------|
| `seed_toronto.py` | Quick 6-step Toronto data seed (parcels, zoning, overlays, dev apps) |
| `seed_toronto_detailed.py` | Full 17-step Toronto seed with per-step control and progress reporting |
| `seed_policies.py` | Seed curated Toronto MVP policy corpus (5 docs, 15 clauses) |
| `seed_reference_data.py` | Seed massing templates, unit types, financial assumptions |
| `railway_seed.py` | Railway deployment seed (downloads from CKAN, supports bbox filter) |
| `ingest_toronto_tracks_1_2.py` | CLI for manual geospatial dataset ingestion (5 subcommands) |
| `audit_toronto_seed.py` | Audit DB state + run benchmark suite against real parcel data |
| `dev_doctor.py` | Preflight connectivity check for local dev environment |
| `generate_sample_dxf.py` | Generate rich sample building DXF (6-storey mixed-use) |
| `generate_sample_pipeline_dxf.py` | Generate sample water main DXF (3x2 junction grid) |
| `railway_seed_full.py` | Full Railway deployment seed (streaming download, chunked ingestion, resume support) |
| `fix_water_mains_download.py` | Patch for corrected CKAN water mains package slug + fallback search |
| `generate_water_main_dxf.py` | Generate DXF from real Toronto water main data (color-coded by material) |
| `test_search.py` | Ad-hoc parcel search test against live DB |
| `init-extensions.sql` | PostgreSQL init (uuid-ossp, postgis, pgvector extensions) |

---

## Tests — `tests/`

24+ test files with pytest + httpx AsyncClient.

| File | Coverage |
|------|----------|
| `conftest.py` | Shared fixtures (httpx AsyncClient via ASGITransport) |
| `test_compliance_engine.py` | Deterministic compliance: FSI, height, lot coverage, parking, angular plane, minor variance |
| `test_zoning_parser.py` | Zone string parsing (12 categories) + standards lookup |
| `test_thin_slice_runtime.py` | Massing, layout, financial models + precedent scoring |
| `test_context_builder.py` | Template placeholder completeness + missing data markers |
| `test_document_selector.py` | Conditional document selection (as-of-right, MV, ZBA, refusal) |
| `test_citation_verifier.py` | By-law section validation + strip unverified citations |
| `test_submission_readiness.py` | Readiness evaluation (blocking issues, placeholders, approval status) |
| `test_geospatial_services.py` | Address normalization, parcel search, canonical address selection |
| `test_geospatial_ingestion.py` | Zone code picking, decision normalization, geometry parsing |
| `test_overlay_service.py` | Overlay dedup, metric sorting, 404 on missing parcel |
| `test_policy_stack.py` | Policy ordering by override level, snapshot dedup |
| `test_policy_seed.py` | Curated corpus structure (5 docs, 15 clauses, 5 override levels) |
| `test_benchmarks.py` | Benchmark fixture loading, case evaluation, suite summarization |
| `test_governance.py` | Manifest hash stability, export control decisions |
| `test_validation.py` | Source metadata, policy rule, precedent, finance record validation |
| `test_dependencies.py` | JWT auth: DB role overrides JWT claim, multi-org 403 |
| `test_assistant_router.py` | Chat endpoint: 503 without key, prompt structure verification |
| `test_plans.py` | Plan generation auth guard (401 without token) |
| `test_health.py` | Health endpoint returns status + version |
| `test_parcels.py` | Parcel search validation + zoning analysis payload structure |
| `test_job_service.py` | Job status serialization across async tables |
| `test_dev_architecture.py` | Docker compose structure, .env.example validation |
| `test_audit_toronto_seed.py` | Benchmark suite execution without DB |
| `test_cache.py` | Redis cache-aside: hit, miss, Redis down, fetch error, TTL (all mocked) |
| `fixtures/benchmarks/` | 3 fixture files: toronto_core.json, toronto_phase2.json, toronto_showcase.json |

---

## Data & Infrastructure Files

| Path | Purpose |
|------|---------|
| `data/property-boundaries-4326.geojson` | Toronto property parcels (WGS84) |
| `data/zoning-area-4326.geojson` | Zoning designations |
| `data/zoning-building-setback-overlay-4326.geojson` | Setback overlays |
| `data/zoning-height-overlay-4326.geojson` | Height restriction overlays |
| `data/development-applications.json` | CoA/ZBA/OPA precedent records (UTM coords) |
| `data/test_floor_plan.dxf` | Sample DXF for parser testing |
| `water-system-data/` | Distribution mains GeoJSON + waterbodies shapefile (other layers removed — ingested into pipeline_assets) |
| `Road/` | Road Reconstruction Program GeoJSON (LineString) |
| `City-electric-charge/` | City-operated EV charging stations GeoJSON (Point) |

---

## Config & DevOps

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Infra-only compose: PostGIS 16, Redis 7, MinIO |
| `docker-compose.app.yml` | App compose override: Celery worker + API + Next.js frontend (containerized) |
| `Dockerfile` | Python-only backend build (no frontend stage) |
| `frontend/Dockerfile` | Next.js standalone build (multi-stage: builder + runner) |
| `frontend/src/app/api.js` | Next.js API client (all backend calls, 401 auto-retry via session exchange) |
| `frontend/src/app/api/auth/exchange/route.ts` | Next.js route: exchanges Better Auth session cookie for FastAPI JWT |
| `railway.toml` | Railway API service config (pre-deploy: alembic migrate, health: /api/v1/health) |
| `alembic.ini` | Alembic migration config |
| `alembic/` | 13 migrations: initial 34-table schema → infrastructure assets → infra data refactor → fact tables → esa_flag → project workspace → fix electrical asset_type |
| `pyproject.toml` | Python project config (uv), Python ≥3.11, pytest asyncio_mode=auto |
| `Makefile` | 12 targets: infra-up/down, doctor, migrate, run-api/frontend, seed, test |
| `.env.example` | Environment variable template (localhost targets) |
| `PLAN.md` | Architecture design document (995 lines, 5 backend systems) |
| `FLOOR_PLAN_EDITOR_IMPROVEMENTS.md` | Floor plan editor feature documentation |
| `TOOLBAR_VISUAL_GUIDE.txt` | ASCII art toolbar reference |
| `skills-lock.json` | Claude skills lock file (neon-postgres) |
| `uv.lock` | UV dependency lock file |

---

## API Endpoint Reference (105 endpoints)

### Auth & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register user + org, returns JWT |
| `POST` | `/api/v1/auth/login` | Login, returns JWT |
| `POST` | `/api/v1/auth/session-exchange` | Exchange Better Auth session token for FastAPI JWT (auto-creates user/org on first login) |
| `GET` | `/api/v1/health` | DB + Redis + Celery liveness check |

### Parcels (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/parcels/search` | Search parcels by address/bbox/zone |
| `GET` | `/api/v1/parcels/{id}` | Get parcel detail with GeoJSON |
| `GET` | `/api/v1/parcels/{id}/zoning-analysis` | Full zoning analysis (components, standards, overlays) |
| `GET` | `/api/v1/parcels/{id}/policy-stack` | Applicable policy stack (ChromaDB RAG) |
| `GET` | `/api/v1/parcels/{id}/overlays` | Overlay layers intersecting parcel |
| `GET` | `/api/v1/parcels/{id}/nearby-applications` | Dev applications within radius |
| `GET` | `/api/v1/parcels/{id}/financial-summary` | Quick financial feasibility snapshot |

### Plans (14 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/plans/generate` | Submit NL query, enqueue plan pipeline |
| `GET` | `/api/v1/plans` | List all plans for org |
| `GET` | `/api/v1/plans/{id}` | Get plan with documents |
| `GET` | `/api/v1/plans/{id}/readiness` | Submission readiness assessment |
| `POST` | `/api/v1/plans/{id}/clarify` | Answer clarification questions |
| `GET` | `/api/v1/plans/{id}/documents` | List submission documents |
| `GET` | `/api/v1/plans/{id}/documents/{doc_id}` | Get single document |
| `POST` | `/api/v1/plans/{id}/documents/{doc_id}/submit-review` | Send doc to human review |
| `POST` | `/api/v1/plans/{id}/documents/{doc_id}/approve` | Approve reviewed document |
| `POST` | `/api/v1/plans/{id}/documents/{doc_id}/reject` | Reject reviewed document |
| `POST` | `/api/v1/plans/{id}/generate-document/{type}` | Generate/regenerate one document type |
| `GET` | `/api/v1/plans/{id}/documents/{doc_id}/download` | Download as markdown/html/docx |
| `POST` | `/api/v1/plans/{id}/export` | Export all plan docs as DOCX |
| `GET` | `/api/v1/plans/{id}/contractors` | Recommend local contractors (Google Places) |

### Assistant (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/assistant/chat` | Multi-turn planning chat (RAG + fine-tuned model) |
| `POST` | `/api/v1/assistant/parse-model` | Parse NL building description into 3D params |
| `POST` | `/api/v1/assistant/parse-infra-model` | Parse NL infrastructure description into params |

### Projects & Scenarios (21 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/projects` | Create project |
| `GET` | `/api/v1/projects` | List projects for org (with counts) |
| `GET` | `/api/v1/projects/{id}` | Get project (with counts) |
| `PATCH` | `/api/v1/projects/{id}` | Update project |
| `DELETE` | `/api/v1/projects/{id}` | Delete project |
| `POST` | `/api/v1/projects/{id}/parcels` | Link parcel to project |
| `DELETE` | `/api/v1/projects/{id}/parcels/{parcel_id}` | Unlink parcel |
| `POST` | `/api/v1/projects/{id}/notes` | Create note |
| `GET` | `/api/v1/projects/{id}/notes` | List notes (pinned first) |
| `PATCH` | `/api/v1/projects/{id}/notes/{note_id}` | Update/pin note |
| `DELETE` | `/api/v1/projects/{id}/notes/{note_id}` | Delete note |
| `POST` | `/api/v1/projects/{id}/conversations` | Save conversation |
| `GET` | `/api/v1/projects/{id}/conversations` | List conversations (summaries) |
| `GET` | `/api/v1/projects/{id}/conversations/{conv_id}` | Get full conversation |
| `PUT` | `/api/v1/projects/{id}/conversations/{conv_id}` | Update conversation messages |
| `DELETE` | `/api/v1/projects/{id}/conversations/{conv_id}` | Delete conversation |
| `GET` | `/api/v1/projects/{id}/plans` | List plans for project |
| `GET` | `/api/v1/projects/{id}/uploads` | List project files |
| `POST` | `/api/v1/projects/{id}/uploads` | Upload file to project |
| `PATCH` | `/api/v1/projects/{id}/map-state` | Save map state |
| `POST` | `/api/v1/projects/{id}/scenarios` | Create scenario run |
| `GET` | `/api/v1/scenarios/{id}` | Get scenario |
| `GET` | `/api/v1/scenarios/{id}/compare/{other_id}` | Compare two scenarios |

### Simulation (6 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scenarios/{id}/massings` | Start massing generation |
| `GET` | `/api/v1/massings/{id}` | Get massing result |
| `GET` | `/api/v1/reference/massing-templates` | List massing templates |
| `GET` | `/api/v1/reference/unit-types` | List unit types |
| `POST` | `/api/v1/massings/{id}/layout-runs` | Start layout optimization |
| `GET` | `/api/v1/layout-runs/{id}` | Get layout result |

### Entitlement & Precedent (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scenarios/{id}/entitlement-runs` | Start entitlement check |
| `GET` | `/api/v1/entitlement-runs/{id}` | Poll entitlement result |
| `POST` | `/api/v1/scenarios/{id}/precedent-searches` | Start precedent search |
| `GET` | `/api/v1/precedent-searches/{id}` | Poll precedent result |

### Finance (3 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/scenarios/{id}/financial-runs` | Start financial analysis |
| `GET` | `/api/v1/financial-runs/{id}` | Get financial result |
| `GET` | `/api/v1/reference/financial-assumption-sets` | List assumption sets |

### Uploads (7 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/uploads` | Upload file (DXF parsed inline, others via Celery) |
| `GET` | `/api/v1/uploads` | List uploads for org |
| `GET` | `/api/v1/uploads/{id}` | Get upload status + extracted data |
| `GET` | `/api/v1/uploads/{id}/pages` | Get page images as presigned S3 URLs |
| `GET` | `/api/v1/uploads/{id}/analysis` | Get extracted data + compliance findings |
| `POST` | `/api/v1/uploads/{id}/generate-plan` | Feed extracted data into plan pipeline |
| `POST` | `/api/v1/uploads/{id}/generate-response` | Generate response doc from findings |

### Ingestion (14 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/admin/ingest/building-permits` | Trigger building permit CKAN ingestion |
| `POST` | `/api/v1/admin/ingest/coa-applications` | Trigger CoA application ingestion |
| `POST` | `/api/v1/admin/ingest/water-mains` | Trigger water main ingestion |
| `POST` | `/api/v1/admin/ingest/sanitary-sewers` | Trigger sanitary sewer ingestion |
| `POST` | `/api/v1/admin/ingest/storm-sewers` | Trigger storm sewer ingestion |
| `POST` | `/api/v1/admin/ingest/bridges` | Trigger bridge inventory ingestion |
| `GET` | `/api/v1/admin/ingest/status` | Ingestion status + dataset counts |
| `POST` | `/api/v1/admin/ingest/arcgis/parcels` | ArcGIS Phase 1: parcels + addresses + current facts |
| `POST` | `/api/v1/admin/ingest/arcgis/buildings` | ArcGIS Phase 2: building footprints + building facts |
| `POST` | `/api/v1/admin/ingest/arcgis/zoning` | ArcGIS Phase 3: zoning areas + zoning facts |
| `POST` | `/api/v1/admin/ingest/arcgis/constraints` | ArcGIS Phase 4: heritage, ravine, ESA + constraint facts |
| `POST` | `/api/v1/admin/ingest/arcgis/full` | All 4 ArcGIS phases sequentially |
| `GET` | `/api/v1/admin/ingest/arcgis/status` | ArcGIS job status + fact table counts |

### Infrastructure (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/infrastructure/pipelines/nearby` | Nearby pipeline assets (GeoJSON) |
| `POST` | `/api/v1/infrastructure/compliance/pipeline` | Pipeline compliance check |
| `GET` | `/api/v1/infrastructure/watermains/bbox` | Water main segments in viewport (from pipeline_assets) |
| `GET` | `/api/v1/infrastructure/sewers/bbox` | Sewer segments in viewport (sanitary + storm from pipeline_assets) |
| `GET` | `/api/v1/infrastructure/electrical/bbox` | Electrical assets in viewport (from electrical_assets) |
| `GET` | `/api/v1/infrastructure/electrical/nearby` | Nearby electrical assets (GeoJSON) |
| `GET` | `/api/v1/infrastructure/electrical/standards` | Ontario electrical standards reference |
| `POST` | `/api/v1/infrastructure/electrical/capacity-check` | Grid capacity check for proposed building |

### Billing (11 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/billing/subscriptions` | Create Stripe subscription |
| `DELETE` | `/api/v1/billing/subscriptions/{id}` | Cancel subscription |
| `POST` | `/api/v1/billing/portal` | Create Stripe customer portal session |
| `POST` | `/api/v1/billing/tokens/purchase` | Purchase token package |
| `POST` | `/api/v1/billing/tokens/consume` | Consume tokens (subscription balance first, then purchased) |
| `GET` | `/api/v1/billing/tokens/balance` | Get token balance (both buckets) |
| `PUT` | `/api/v1/billing/tokens/topup-config` | Configure auto top-up threshold |
| `POST` | `/api/v1/billing/usage` | Record usage event |
| `POST` | `/api/v1/billing/invoices/generate` | Generate invoice for org |
| `GET` | `/api/v1/billing/invoices/{org_id}` | List invoices for org |
| `POST` | `/api/v1/webhooks/stripe` | Stripe webhook handler |

### Compliance, Exports, Design, Governance, Policy, Jobs (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/compliance/interior` | OBC interior compliance check |
| `POST` | `/api/v1/exports` | Create export job |
| `GET` | `/api/v1/exports/{id}` | Get export result |
| `POST` | `/api/v1/designs/{project_id}/branches` | Create design branch |
| `GET` | `/api/v1/designs/{project_id}/branches` | List branches |
| `DELETE` | `/api/v1/designs/{project_id}/branches/{id}` | Delete branch |
| `POST` | `/api/v1/designs/branches/{id}/commit` | Commit version |
| `GET` | `/api/v1/designs/branches/{id}/versions` | List versions |
| `GET` | `/api/v1/designs/branches/{id}/latest` | Get latest version |
| `GET` | `/api/v1/designs/versions/{id}` | Get specific version |
| `GET` | `/api/v1/snapshot-manifests/{id}` | Get manifest (admin) |
| `GET` | `/api/v1/review-queue` | List review items (admin) |
| `GET` | `/api/v1/policies/search` | Policy search (stub) |
| `POST` | `/api/v1/scenarios/{id}/policy-overrides` | Policy overrides (stub) |
| `GET` | `/api/v1/jobs/{id}` | Generic job status polling |

---

## Running Locally

```bash
# Backend
uvicorn app.main:app --reload

# Frontend (Next.js)
cd frontend && npm run dev

# Docker (all services)
docker compose -f docker-compose.yml -f docker-compose.app.yml up

# RAG (optional, for policy retrieval)
cd fine-tuned-RAG && python api.py
```
