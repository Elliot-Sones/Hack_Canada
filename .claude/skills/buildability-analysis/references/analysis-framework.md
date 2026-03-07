---
title: "Buildability Analysis Framework"
category: buildability-analysis
relevance: "Load when running dimensional compliance checks, overlay assessments, O.Reg 462/24 override logic, or confidence scoring. Contains the full 6-stage analysis checklist."
key_topics: "Parcel ID, zoning classification, OP designation, overlays, heritage, TRCA, O.Reg 462/24 multiplex override, confidence scoring, Green/Yellow/Red verdicts, mandatory disclaimer"
---

# Buildability Analysis Framework

## Feasibility Signal Model

The Green/Yellow/Red feasibility verdict follows the same model as the Toronto Hydro Load Capacity Map:
- **Green**: High available capacity / high feasibility — project can proceed with confidence
- **Yellow**: Moderate constraints — process required, outcome uncertain but achievable
- **Red**: Severe constraints / high likelihood of expensive process or prohibition

## Confidence Scoring Basis

Toronto Open Data uses a **Data Quality Score (DQS)**: Freshness (35%), Metadata (35%), Accessibility (15%), Completeness (10%), Usability (5%). Gold datasets (>80%) should be preferred. Apply the same weighting logic when evaluating confidence in extracted data.

---

## Core Principle

Every finding must be classified into one of four categories:

| Category | Definition | Confidence |
|----------|-----------|-----------|
| **Confirmed Fact** | Directly verifiable from a cited public source | High |
| **Structured Inference** | Logically derived from confirmed facts using stated rules | Medium |
| **Assumption** | Working assumption needed to proceed; stated explicitly | Low |
| **Unknown** | Cannot be determined from public sources | Flagged |

---

## Analysis Checklist (Run in Order)

### Stage 1: Parcel Identification
- [ ] Resolve input address to a valid Toronto Address Point
- [ ] Obtain coordinates (lat/lon)
- [ ] Obtain PIN from Ontario Parcel layer
- [ ] Record lot frontage and depth (from MPAC or address point data)
- [ ] Calculate or confirm lot area

**Flag if**: Address cannot be resolved to a unique parcel → stop pipeline, return error.

---

### Stage 2: Zoning Classification
- [ ] Query Toronto Zoning By-law 569-2013 spatial layer at parcel coordinates
- [ ] Extract zone code (e.g., RD, RS, CR)
- [ ] Check if parcel is in a "Hatched Area" (legacy by-law zone)
- [ ] Check Chapter 900 for site-specific exceptions (flag for human review — no automated check)
- [ ] Record data freshness of zoning layer (flag if >90 days old)
- [ ] Check for active Zoning By-law Amendments (ZBAs) on the parcel via AIC/Development Applications

**Confidence rules:**
- Hatched Area detected → confidence = "inferred" for all zone standards
- Active ZBA on parcel → confidence = "inferred" (rules may change)
- Standard 569-2013 zone, no ZBA → confidence = "confirmed"

---

### Stage 3: Official Plan Designation
- [ ] Query Toronto OP land use layer at parcel coordinates
- [ ] Record designation (e.g., Neighbourhoods, Mixed Use Areas)
- [ ] Check if parcel falls within a Secondary Plan area
- [ ] Check if parcel falls within a Site and Area Specific Policy (SASP)
- [ ] Confirm OP designation is compatible with proposed project type

**Compatibility check:**

| Proposed Project | Compatible OP Designations | Incompatible |
|-----------------|---------------------------|--------------|
| Detached / Semi / Multiplex | Neighbourhoods, Apt. Neighbourhoods | Employment Areas |
| Mid-rise Mixed-Use | Mixed Use Areas, Apt. Neighbourhoods | Neighbourhoods |
| Garden / Laneway Suite | Neighbourhoods, Mixed Use | Employment, Natural Areas |
| Commercial | Mixed Use, Employment | Neighbourhoods (generally) |
| Industrial | Employment (EH, EI) | All others |

**Flag if**: Proposed use conflicts with OP designation → "Requires Official Plan Amendment — not as-of-right."

---

### Stage 4: Overlay & Constraint Check

Run all overlay checks in parallel.

#### 4a. Heritage
- [ ] Check Heritage Register for Listed or Designated status
- [ ] Check if parcel is within an HCD (Heritage Conservation District)
- **If Listed**: Flag "Listed property — 60 days' notice required before demolition, allowing City to evaluate for designation. Heritage Impact Assessment may be required." (Limited conservation protection, but delays any demolition.)
- **If Designated (Part IV)**: Flag "Designated heritage property — a specific Heritage by-law is registered on title detailing the exact 'heritage attributes' that must be conserved. Heritage Impact Assessment (HIA) required before any alteration application is filed."
- **If HCD (Part V)**: Flag "Heritage Conservation District — design guidelines apply to all buildings and alterations within the district, regardless of individual designation status."

#### 4b. Environmental / Flood
- [ ] Query TRCA Regulated Area layer
- [ ] If in regulated area: Flag "TRCA permit required in addition to building permit."
- [ ] Query TRCA Floodline layer — note if boundary type is Engineered or Estimated
- **If within Engineered floodplain**: Flag "Development may be prohibited — detailed flood study required."
- **If within Estimated floodplain proximity**: Flag "Physical site survey required — estimated boundary not sufficient for clearance."

#### 4c. Greenbelt
- [ ] Query Greenbelt Plan boundary
- **If intersects**: Flag "Greenbelt constraint — development severely restricted, specialist review required."

#### 4d. Development Application History
- [ ] Query AIC for prior minor variances, consents, ZBAs on the parcel
- [ ] Query Development Applications open data for active applications
- **If active ZBA**: Flag "Active rezoning in progress — base zone standards may change."
- **If prior minor variance approved**: Note — may expand permissions or may have conditions that constrain future development.

#### 4e. Building Permit History
- [ ] Query active and cleared building permits
- **If permits show recent densification**: Note existing units count — affects remaining capacity.

---

### Stage 5: O.Reg 462/24 Multiplex Override Check

*Only applies if proposed project type = multiplex / additional residential units*

- [ ] Check if proposed lot coverage exceeds the base ZBL limit
- [ ] Check if base ZBL applies FSI restriction
- [ ] Apply O.Reg 462/24 override:
  - Is lot coverage under the ZBL more restrictive than 45–60%? → O.Reg may permit more.
  - Does ZBL restrict ARUs via FSI? → O.Reg 462/24 removes FSI for additional units.
  - Is parking required by ZBL for these units? → O.Reg 462/24 requires 0 minimum.
- **Result**: State whether the project is feasible under 569-2013 alone, or requires the O.Reg 462/24 override, and note which standard applies.

---

### Stage 6: Physical & Technical Constraints (Flag for Human Review)

These cannot be determined from public data. All must be flagged as "Requires Human Review / Technical Study."

| Constraint | Why It Cannot Be Automated | Required Study |
|-----------|--------------------------|----------------|
| Sewer / water servicing capacity | Pipes are mapped; residual flow capacity is not | Functional Servicing Report (FSR) |
| Unregistered easements | Utilities like Hydro One hold unregistered access rights not visible in GIS maps or standard title searches | Title search (OnLand) |
| Established grade (for height) | Public LiDAR ±0.5m accuracy is too coarse for legal zoning height determinations | Site survey |
| Tree protection | No centralized GIS layer for protected trees; a single tree 30cm+ in rear yard can legally block as-of-right garden suite | Urban Forestry pre-consultation |
| Emergency/fire access (OBC) | 1.0m minimum unobstructed path to rear required, maximum travel distance 45m — **cannot be varied by Committee of Adjustment** (Ontario Building Code requirement) | Site plan review |
| Soil contamination | Requires on-site investigation for historical industrial use | Phase 1/2 Environmental Site Assessment |
| Hydro load capacity | Maps show feeder locations but not residual capacity | Toronto Hydro load study |

---

## Confidence Scoring System

Each finding is scored on a 0–1 scale:

| Score | Label | Meaning |
|-------|-------|---------|
| 0.9–1.0 | High | Confirmed from authoritative source with no known staleness or conflicts |
| 0.7–0.89 | Medium | Confirmed from source with known limitations (e.g., zoning layer >90 days old) |
| 0.5–0.69 | Low | Inferred from general rules (e.g., hatched area, active ZBA) |
| 0.0–0.49 | Very Low / Unknown | Cannot be confirmed from public data; human review required |

**Overall feasibility confidence = lowest confidence score among Stage 2–5 checks**

---

## Output: Feasibility Finding Categories

### Green — As-of-Right Likely
- Zone permits the proposed use
- OP designation compatible
- No blocking overlays
- Development standards (height, FSI, lot coverage) met
- No active ZBAs or major applications
- *But always note: Chapter 900, physical constraints, and technical studies still required*

### Yellow — Feasible with Process
- Minor variance likely required for a specific standard deviation
- Heritage listed (not designated) — assessment required but not prohibitive
- Active nearby development application may affect context

### Red — Significant Constraint
- Zone does not permit the proposed use → ZBL Amendment required
- OP designation incompatible → OPA required
- Heritage designated (Part IV) — complex heritage process
- TRCA Regulated Area with Engineered floodplain
- Hatched area with unknown legacy by-law standards

### Unknown — Insufficient Data
- Hatched area with legacy by-law not available online
- Chapter 900 exception suspected but not confirmed
- **Active OLT appeal in progress**: A zoning map may display a newly enacted height or density limit, but if that amendment is under active OLT appeal, the legally "in-force" standard remains the **pre-amendment standard** until the tribunal decides. Always check OLT case search for active appeals before treating zoning map data as current law.

---

## Mandatory Disclaimer Text

All reports must include:

> "This assessment is based on publicly available data as of [date]. It is a preliminary screening tool only and does not constitute professional planning, legal, or architectural advice. Open data web maps and consolidations are provided for convenience only and do not have legal status. Digital constraint maps (including those from Toronto Water and TRCA) do not replace detailed engineering studies or diligent field examinations and should not be relied upon for precise legal limits. Zoning data may not reflect recent Council amendments or OLT appeal outcomes. For legal and planning application purposes, the original certified documents on file with the City Clerk and the Land Registry Office are the final legal arbiters. Chapter 900 site-specific exceptions, physical site constraints, and technical infrastructure capacity cannot be fully assessed from public data alone. Consult a qualified planner, architect, or solicitor before making development decisions."
