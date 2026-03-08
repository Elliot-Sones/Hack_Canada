# PRD: CoCivil — Land-Development Due Diligence Platform

> **Last updated**: 2026-03-08
> **Status**: MVP (v0.1.0) — Toronto / Ontario jurisdiction
> **Platform name**: CoCivil

---

## 1. Executive Summary

CoCivil is a full-stack land-development due diligence platform that transforms a plain-English development query into a structured, source-backed submission package. It combines deterministic zoning compliance, AI-assisted policy extraction, 3D massing visualization, 2D floor-plan editing with OBC compliance checks, financial pro-forma modeling, precedent research, and entitlement-pathway classification — all within a single authenticated workspace.

The system is built for speed and defensibility: compliance rules are deterministic (no AI), AI is constrained to cite only sources provided in context, and every output is versioned and auditable.

---

## 2. Problem Statement

Early-stage site feasibility for real estate development is slow, fragmented, and error-prone:

| Pain Point | Impact |
|------------|--------|
| Policy scattered across zoning by-laws, Official Plans, overlays, and provincial bills | 10–40 hours of manual research per site |
| No standard way to distinguish hard rules from soft guidance or unknowns | Inconsistent assessments across teams |
| Compliance matrices built manually in Excel | High error rate, non-reproducible |
| Precedent research requires manual searches across AIC, OLT, CanLII | Days of legal research per project |
| 3D massing and unit-mix optimization done in separate tools | Disjointed workflow, version confusion |
| No audit trail connecting policy citations to generated documents | Hard to defend outputs in formal submissions |

---

## 3. Product Vision

> **"One query. One workspace. A defensible feasibility package."**

A developer, acquisitions analyst, or planning consultant types a plain-English development concept (e.g., *"10-storey mixed-use on Bloor near Lansdowne"*) and receives:

1. **Parcel resolution** — address geocoded, parcel retrieved, zone code identified
2. **Policy stack** — Planning Act → PPS → Toronto OP → Zoning By-law 569-2013, Bills 23/185/60
3. **Compliance matrix** — deterministic check of FSI, height, setbacks, lot coverage, parking, amenity
4. **Massing envelope** — parametric 3D building (viewable in-browser), GFA, unit count, storey count
5. **Unit mix & layout** — optimized floor-plan unit distribution, interior OBC compliance
6. **Financial pro forma** — revenue, construction cost, NOI, cap rate, IRR
7. **Precedent report** — nearby CoA/ZBA decisions ranked by similarity
8. **Entitlement assessment** — approval pathway (as-of-right / CoA / ZBA / OPA) with timeline
9. **Submission package** — Planning Rationale, Compliance Matrix, Precedent Report — PDF, audit-ready

---

## 4. Goals and Non-Goals

### Goals

- Reduce initial site-feasibility research from days to minutes
- Generate structured, traceable, source-backed outputs for real development queries
- Provide deterministic compliance (no AI guessing at rules)
- Integrate 3D visualization and 2D floor-plan editing in one workspace
- Support a collaborative multi-tenant workspace with version-controlled designs
- Enforce policy citations: AI cites only sources provided in context
- Build an MVP scoped to Toronto/Ontario before expanding geographically

### Non-Goals

- Replacing licensed planners, architects, lawyers, or engineers
- Issuing legal advice or stamped compliance documents
- Guaranteeing permit or entitlement outcomes
- Supporting all Canadian municipalities at launch
- Producing construction-ready drawings or structural engineering
- Accessing restricted or paid data sources without explicit integration

---

## 5. Target Users

### Primary

| User Type | Core Job | Key Pain |
|-----------|----------|----------|
| Real estate developer / principal | Evaluate new site acquisitions fast | Manual research, inconsistent team outputs |
| Land acquisition analyst | Screen 20–50 sites per quarter | No scalable workflow for policy research |
| Urban planning consultant | Prepare submission packages | Formatting, sourcing, version management |
| Architecture firm (planning dept.) | Feasibility and zoning compliance | Switching between tools (CAD, Excel, GIS) |

### Secondary

| User Type | Core Job |
|-----------|----------|
| Proptech operator | Resell feasibility-as-a-service to clients |
| Municipal policy researcher | Study zoning patterns and development trends |
| Investment fund analyst | Underwrite land values at portfolio scale |
| Planning student / startup | Build feasibility tooling, learn planning law |

---

## 6. Core User Journey

```
1. Sign In (Auth0)
         ↓
2. Search Address (SearchBar → Nominatim geocoder → Parcel resolved)
         ↓
3. View Parcel on Map (MapLibre GL, Toronto 3D basemap)
         ↓
4. Chat / Query (ChatPanel)
   "Build 80 units, mixed-use, 10 storeys on this site"
         ↓
5. Plan Generation (async Celery pipeline)
   Policy → Compliance → Massing → Layout → Finance → Precedents → Docs
         ↓
6. Review Results (PolicyPanel — 7 tabs)
   Overview | Massing | Policies | Datasets | Precedents | Entitlements | Finances
         ↓
7. 3D Model Viewer (ModelViewer)
   Rotate massing | Switch floor | View unit mix | Floor plan mode
         ↓
8. 2D Floor Plan Editor (FloorPlanEditor)
   Draw walls | Add rooms/openings | OBC compliance badges live
         ↓
9. Design Version Control
   Commit design | Create branch | Review history
         ↓
10. Export / Submit
    PDF submission package | Governance-stamped documents
```

---

## 7. Feature Inventory

### 7.1 Parcel & Map Layer

| Feature | Status | Notes |
|---------|--------|-------|
| Address geocoding (Nominatim, Toronto-scoped) | ✅ Done | SearchBar.jsx, 350ms debounce |
| Parcel resolution (PostGIS spatial query) | ✅ Done | `GET /api/v1/parcels/search` |
| MapLibre GL 3D map (OSM basemap, 60° pitch) | ✅ Done | MapView.jsx |
| Parcel outline overlay on map | ✅ Done | GeoJSON FillLayer + LineLayer |
| Proposed massing overlay on map | ✅ Done | 3D extrusion when massing resolved |
| Parcel zoning assignment | ✅ Done | `ParcelZoningAssignment` model |
| GIS overlay intersection (heritage, flood) | ✅ Done | `overlay_service.py` |
| Nearby development applications (spatial) | ✅ Done | `GET /api/v1/parcels/{id}/nearby-applications` |

### 7.2 Policy Stack & Compliance Engine

| Feature | Status | Notes |
|---------|--------|-------|
| Policy hierarchy builder (Planning Act → SPC) | ✅ Done | `policy_stack.py` |
| Hardcoded By-law 569-2013 zone standards | ✅ Done | `toronto_zoning.py` (R, RM, CR, DL, IH, IO, IE, IL) |
| Ontario policy constants (Bills 23/185/60/60) | ✅ Done | `ontario_policy.py` |
| Deterministic compliance engine (no AI) | ✅ Done | `compliance_engine.py` — lot coverage, FSI, height, setbacks, parking, amenity |
| OBC interior compliance (Part 9) | ✅ Done | `interior_compliance.py` — bedroom, egress, hallway, ceiling, fire |
| Compliance matrix API | ✅ Done | `POST /api/v1/entitlement/compliance` |
| Policy document versioning (PolicyVersion) | ✅ Done | `models/policy.py` |
| AI-constrained citation (grounding instruction) | ✅ Done | `_GROUNDING_INSTRUCTION` in `templates.py` |

### 7.3 Plan Generation Pipeline

| Feature | Status | Notes |
|---------|--------|-------|
| Natural language query parser | ✅ Done | `query_parser.py` (uses Claude) |
| Celery async pipeline orchestration | ✅ Done | `tasks/plan.py` |
| Plan state machine (pending → generating → complete/failed) | ✅ Done | `DevelopmentPlan.status` |
| Safety preamble on all AI docs | ✅ Done | `SAFETY_PREAMBLE` prepended automatically |
| Document readiness check | ✅ Done | `readiness.py` |
| AI document review | ✅ Done | `review.py` |
| Citation verifier | ✅ Done | `citation_verifier.py` |
| Plan regeneration / clarification | ✅ Done | `POST /api/v1/plans/{id}/clarify` |

### 7.4 Massing & Simulation

| Feature | Status | Notes |
|---------|--------|-------|
| Parametric massing envelope (height, GFA, FSI, geom) | ✅ Done | `simulation_runtime.py` |
| Unit mix optimization (1BR/2BR/3BR) | ✅ Done | `tasks/layout.py` |
| Massing templates (midrise, tower, townhouse, slab) | ✅ Done | `thin_slice_runtime.py` |
| 3D massing typologies in viewer | ✅ Done | `ModelViewer.jsx` — floor-plate geometry by typology |
| Floor selector in 3D viewer | ✅ Done | ModelViewer floor state |
| Interior 3D view mode | ✅ Done | ModelViewer "interior" mode |
| Blueprint view mode | ✅ Done | ModelViewer "blueprint" mode |
| Massing → Map overlay sync | ✅ Done | 3D extrusion on MapView when massing resolved |

### 7.5 2D Floor Plan Editor

| Feature | Status | Notes |
|---------|--------|-------|
| Konva canvas-based floor plan editor | ✅ Done | `FloorPlanEditor.jsx` |
| Wall drawing tool (exterior / interior) | ✅ Done | `WallLayer.jsx` |
| Room placement with type and color | ✅ Done | `RoomLayer.jsx`, `RoomTypeSelector.jsx` |
| Door / window openings | ✅ Done | `OpeningLayer.jsx` (swing arc, parallel lines) |
| Auto-generated dimension annotations | ✅ Done | `DimensionLayer.jsx` |
| Snap-to-grid | ✅ Done | `wallGeometry.js` |
| Undo / redo | ✅ Done | FloorPlanEditor history stack |
| Scale calibration (manual + two-point) | ✅ Done | `ScaleCalibration.jsx` |
| Load-bearing wall detection | ✅ Done | `interior_compliance.py` heuristic |
| Real-time OBC compliance badges | ✅ Done | `ComplianceBadgeLayer.jsx` — debounced API calls |
| OBC compliance panel (violations list) | ✅ Done | `CompliancePanel.jsx` |
| Wall properties inspector | ✅ Done | `WallProperties.jsx` (load-bearing toggle, thickness) |
| DXF floor plan parsing (ezdxf) | ✅ Done | `dxf_parser.py` — extracts walls/rooms/openings |
| DXF upload → auto-populate editor | ✅ Done | `POST /api/v1/uploads/` + document_analysis task |

### 7.6 Design Version Control

| Feature | Status | Notes |
|---------|--------|-------|
| Design branches (DesignBranch model) | ✅ Done | `design_version_service.py` |
| Design commits (DesignVersion model) | ✅ Done | Commit with auto-compliance snapshot |
| Branch selector in ModelViewer | ✅ Done | `ModelViewer.jsx` version control bar |
| Commit history panel | ✅ Done | ModelViewer history panel |
| Discard changes | ✅ Done | Reverts to last committed state |
| Compliance snapshot on commit | ✅ Done | OBC findings stored with each version |

### 7.7 Financial Pro Forma

| Feature | Status | Notes |
|---------|--------|-------|
| Financial assumption sets | ✅ Done | `FinancialAssumptionSet` model |
| Pro forma runs (revenue, cost, NOI, cap rate, IRR) | ✅ Done | `tasks/finance.py` |
| Assessed value + market comps display | ✅ Done | Finances tab in PolicyPanel |
| Financial summary API | ✅ Done | `GET /api/v1/parcels/{id}/financial-summary` |

### 7.8 Precedent Research

| Feature | Status | Notes |
|---------|--------|-------|
| Spatial precedent search (nearby applications) | ✅ Done | `precedent.py` |
| Scoring (distance, height delta, units delta, FSI delta, decision) | ✅ Done | Weighted score in `precedent.py` |
| Precedent display (distance, decision badge) | ✅ Done | Precedents tab in PolicyPanel |
| PrecedentSearch / PrecedentMatch models | ✅ Done | `models/entitlement.py` |
| AIC / OLT / CanLII source references | 🔄 Partial | Skills describe research method; direct API not integrated |

### 7.9 Entitlement Assessment

| Feature | Status | Notes |
|---------|--------|-------|
| Approval pathway classification (as-of-right / CoA / ZBA / OPA) | ✅ Done | Entitlement tab, `approval-pathway` skill |
| Four-test variance assessment | ✅ Done | `ontario_policy.py` |
| Bill 185 zero parking rule | ✅ Done | `ontario_policy.py` |
| Bill 60 as-of-right residential variances | ✅ Done | `ontario_policy.py` |
| O.Reg 462/24 multiplex rules | ✅ Done | `ontario_policy.py` |
| OBC hard constraints (cannot be varied by CoA) | ✅ Done | `obc_interior_standards.py`, skills references |
| Entitlement pathway badges UI | ✅ Done | Entitlements tab in PolicyPanel |

### 7.10 AI Assistant

| Feature | Status | Notes |
|---------|--------|-------|
| Multi-turn AI chat | ✅ Done | `ChatPanel.jsx`, `POST /api/v1/assistant/chat` |
| Plan-generation command from chat | ✅ Done | `chatCommands.js` regex parser |
| Upload and analyze from chat | ✅ Done | File drag-drop, 50MB limit, `chatCommands.js` |
| Upload-to-plan command | ✅ Done | `PLAN_FROM_UPLOAD_RE` regex |
| Model / floor-plan view commands | ✅ Done | `MODEL_RE`, `FLOOR_RE`, `VIEW_MODE_RE` |
| Branch / commit commands from chat | ✅ Done | `BRANCH_RE`, `COMMIT_RE` |
| Claude provider abstraction | ✅ Done | `ai/factory.py` — Claude or OpenAI at runtime |

### 7.11 Multi-Tenant Workspace

| Feature | Status | Notes |
|---------|--------|-------|
| Organization model | ✅ Done | `Org`, `WorkspaceMember` |
| User registration / JWT auth | ✅ Done | `POST /api/v1/auth/register`, `/login` |
| Auth0 frontend integration | ✅ Done | `@auth0/auth0-react` |
| Project model (container for parcels + plans) | ✅ Done | `Project` model |
| Project parcel linking | ✅ Done | `ProjectParcel` association |
| Project sharing | ✅ Done | `ProjectShare` model |
| Row-level RBAC | ✅ Done | `access_control.py` |
| Governance controls (export, audit events) | ✅ Done | `models/governance.py`, `export.py` |
| Idempotency (API key deduplication) | ✅ Done | `idempotency.py` middleware |

### 7.12 Data Ingestion

| Feature | Status | Notes |
|---------|--------|-------|
| Toronto Open Data CKAN API client | ✅ Done | `ckan_ingestion.py` |
| Building permits ingestion | ✅ Done | `tasks/ingestion.py` |
| CoA applications ingestion | ✅ Done | `tasks/ingestion.py` |
| PostGIS spatial index on parcels | ✅ Done | `alembic/versions/` |
| SourceSnapshot / IngestionJob tracking | ✅ Done | `models/ingestion.py` |
| Admin ingestion endpoints | ✅ Done | `POST /api/v1/admin/ingest/*` |
| Seed scripts (5 Toronto datasets) | ✅ Done | `scripts/seed_toronto.py` |

---

## 8. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React 19 + Vite, port 5173)                      │
│  Auth0 → JWT → api.js → proxy → FastAPI :8000               │
│  Components: MapView | ModelViewer | FloorPlanEditor         │
│              Sidebar | PolicyPanel | ChatPanel               │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                 │
│  18 routers → 28 services → SQLAlchemy async                │
│  Compliance engine: deterministic (no AI)                   │
│  Submission pipeline: AI-constrained (grounding instruction) │
│  Celery tasks for all long-running operations               │
└─────────────────────────────────────────────────────────────┘
        │               │               │              │
  PostgreSQL+PostGIS  Redis           MinIO (S3)    Claude API
  (parcels, plans,   (task broker,   (documents,   (extraction,
   zoning, models)    results cache)  exports)       generation)
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Compliance engine is deterministic (no AI) | Reproducibility, auditability, compliance is not opinion |
| AI constrained by `_GROUNDING_INSTRUCTION` | Cannot hallucinate policy — must cite provided sources only |
| `SAFETY_PREAMBLE` on all AI documents | Signals outputs are AI-generated and require professional review |
| Celery for all long-running tasks | Plan generation takes 30–120s; async-first prevents request timeouts |
| PostGIS for spatial queries | Native ST_Contains, ST_DWithin, ST_Intersects — essential for parcel + overlay lookups |
| Konva for 2D floor plans | Fast HTML5 Canvas, layer compositing, intuitive React API |
| Three.js/R3F for 3D massing | WebGL performance, declarative R3F API, no native browser 3D limitation |
| MapLibre GL (not Leaflet) | Vector tiles, 3D buildings, pitch/bearing support, open-source |
| Design version control (branches + commits) | Git-like workflow for iterative design — prevents loss of approved states |
| Auth0 frontend + JWT backend | Managed identity (Auth0) + stateless backend verification |

---

## 9. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Auditability** | Every compliance finding has a rule reference; every AI document cites only provided sources |
| **Traceability** | `DevelopmentPlan` links to all parcels, documents, scenarios, versions |
| **Reproducibility** | Compliance engine output is deterministic for same inputs |
| **Scalability** | Celery workers scale horizontally; PostGIS indexed for spatial queries |
| **Security** | JWT auth on all API routes; organization-scoped row isolation; no cross-tenant data leakage |
| **Performance** | Parcel search < 500ms; compliance check < 200ms; plan generation async (202 + polling) |
| **Modifiability** | AI provider swappable at runtime (`AI_PROVIDER=claude/openai`); jurisdiction-agnostic service layer |
| **Deployment** | Docker Compose for local dev; Railway for cloud; `railway.toml` and `railway.worker.toml` |

---

## 10. Data Model Summary

```
Org
 └─ User → WorkspaceMember
 └─ Project → ProjectParcel → Parcel
                └─ ParcelZoningAssignment → ZoningStandard
                └─ ParcelMetric (area, frontage, depth)
                └─ IngestionJob, SourceSnapshot

Project → DevelopmentPlan (state machine)
           └─ SubmissionDocument (planning_rationale, compliance_matrix, precedent_report)
           └─ FinancialRun → FinancialAssumptionSet
           └─ Massing → LayoutRun → UnitType
           └─ PrecedentSearch → PrecedentMatch → DevelopmentApplication

Project → DesignBranch → DesignVersion (floor plan JSON + OBC snapshot)

UploadedDocument → DocumentPage (DXF/PDF parsed content, compliance findings)

PolicyDocument → PolicyVersion → PolicyClause
DatasetLayer → DatasetFeature (GeoJSON overlays: heritage, flood, etc.)
ExportJob, AuditEvent (governance trail)
```

---

## 11. API Surface (Summary)

| Router | Prefix | Key Endpoints |
|--------|--------|---------------|
| Auth | `/api/v1/auth` | `POST /register`, `POST /login` |
| Plans | `/api/v1/plans` | `POST /generate`, `GET /{id}`, `GET /{id}/readiness`, `POST /{id}/clarify` |
| Parcels | `/api/v1/parcels` | `GET /search`, `GET /{id}`, `GET /{id}/policy-stack`, `GET /{id}/overlays`, `GET /{id}/nearby-applications`, `GET /{id}/financial-summary` |
| Projects | `/api/v1/projects` | Full CRUD + parcel linking |
| Assistant | `/api/v1/assistant` | `POST /chat` |
| Compliance | `/api/v1/compliance` | `POST /interior` (OBC, no auth) |
| Entitlement | `/api/v1/entitlement` | `POST /compliance`, `POST /precedent-search` |
| Simulation | `/api/v1/simulation` | `POST /massing`, `POST /layout`, reference templates |
| Finance | `/api/v1/finance` | Pro forma runs, assumption sets |
| Uploads | `/api/v1/uploads` | `POST /`, `GET /{id}/analyze`, `POST /{id}/generate-plan` |
| Design Versions | `/api/v1/design-versions` | Branch CRUD, `POST /{branch}/commit`, `GET /{branch}/history` |
| Ingestion (admin) | `/api/v1/admin/ingest` | `POST /building-permits`, `POST /coa-applications`, `GET /status` |
| Governance | `/api/v1/governance` | Audit events, export jobs |
| Health | `/api/v1/health` | `GET /` (infra health) |

---

## 12. Agent Skills Pipeline

The `.claude/skills/` directory provides 7 self-contained research skills for Ontario site feasibility. They are invoked sequentially as a pipeline:

```
Address Input
    ↓
source-discovery          → source_bundle.json      (official URLs)
    ↓
parcel-zoning-research    → normalized_data.json     (zone, OP, overlays)
    ↓
buildability-analysis     → analysis_packet.json     (feasibility verdict)
precedent-research        → precedent_packet.json    (AIC, OLT, CanLII)
    ↓
constraints-red-flags     → constraints_packet.json  (OBC, risk flags)
approval-pathway          → approval_pathway.json    (route + timeline)
    ↓
report-generator          → final_report.md          (client-facing)
```

Each skill cites only specific reference files — no broad internet search. This enforces source discipline and reproducibility.

---

## 13. Known Gaps & Upcoming Work

### High Priority

| Gap | Impact | Notes |
|-----|--------|-------|
| Real parcel boundaries from Toronto Open Data (not mock geometry) | High | `Parcel.geometry` needs real PostGIS polygons from CKAN shapefile |
| AIC / OLT / CanLII live API integration | High | Precedent skill documents the pattern; live fetch not implemented |
| `DevelopmentApplication.decision` NULL for real data | High | Precedent scoring requires real decision field from CKAN |
| User-facing onboarding flow | High | First-time user experience not designed |
| Stripe billing / plan limits | Medium | Multi-tenant SaaS billing not integrated |

### Medium Priority

| Gap | Impact | Notes |
|-----|--------|-------|
| Scenario comparison (`/scenarios/{id}/compare` — TODO in router) | Medium | Schema and endpoint exist but logic not implemented |
| Multi-jurisdiction support (beyond Toronto) | Medium | Services are jurisdiction-parameterized but data only exists for Toronto |
| Export to PDF (governance-stamped) | Medium | `ExportJob` model exists; PDF rendering not implemented |
| Realtime collaboration (shared workspaces) | Medium | `ProjectShare` model exists; WebSocket not implemented |
| Mobile-responsive UI | Low | Desktop-first; no mobile breakpoints in current CSS |

### Low Priority

| Gap | Impact | Notes |
|-----|--------|-------|
| OpenAI provider completion | Low | Stub exists; only Claude implemented |
| E2E test suite | Low | Unit tests exist; Playwright E2E not wired |
| CI/CD pipeline | Low | Railway deploys manually; no GitHub Actions |

---

## 14. Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| Time from query to plan generation | < 3 minutes (P90) |
| Compliance check accuracy vs. manual review | ≥ 95% (deterministic rules) |
| Plan generation success rate | ≥ 90% (parcel resolved + no Celery failure) |
| OBC compliance badge accuracy | ≥ 90% (Part 9 rules) |
| Precedent match relevance (user rating) | ≥ 4/5 average |
| Document citation accuracy | 100% (grounding instruction enforced) |
| User session retention (first plan → second plan) | ≥ 60% |

---

## 15. Out of Scope

- Legal advice or formally stamped compliance documents
- Guaranteeing permit or entitlement outcomes
- Structural, mechanical, or electrical engineering
- Construction cost estimating (beyond high-level pro forma)
- Real-time municipal data feeds (polling, not streaming)
- Support for non-Ontario jurisdictions at launch
- Native mobile apps (iOS / Android)
- Offline mode

---

## 16. Deployment

| Environment | Infrastructure | Notes |
|-------------|----------------|-------|
| Local dev | Docker Compose | `docker-compose.yml` — db (PostGIS), redis, minio, api, worker, beat |
| Production | Railway | `railway.toml` (API), `railway.worker.toml` (Celery worker) |
| Storage | MinIO (dev) / S3 (prod) | S3-compatible, presigned URLs for document access |
| Database | PostgreSQL 15 + PostGIS | pgvector extension for future embedding search |

---

*This PRD reflects the platform as of v0.1.0 (2026-03-08). Platform renamed from Arterial to CoCivil. Supersedes the earlier "Buildability Intelligence Pipeline" PRD which described the pre-MVP pipeline concept.*
