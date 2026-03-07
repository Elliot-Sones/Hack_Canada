---
name: parcel-zoning-research
version: "1.0"
description: "Extracts and normalizes parcel, zoning, Official Plan, and overlay facts from a previously discovered Ontario source bundle. This skill should be used when `source_bundle.json` exists and the pipeline needs a source-backed `normalized_data.json` for downstream analysis."
source: "Toronto Zoning By-law 569-2013, Toronto Official Plan, Ontario Parcel (LIO), TRCA"
authority: "City of Toronto, Province of Ontario"
data_as_of: "2026-03-07"
pipeline_position: 2
pipeline_inputs: "source_bundle.json"
pipeline_outputs: "normalized_data.json"
pipeline_upstream: "source-discovery"
pipeline_downstream: "buildability-analysis, precedent-research"
---

# Parcel Zoning Research

## Purpose

Convert a discovered source inventory into one normalized, source-backed parcel record. This skill performs extraction and normalization. It does not render a feasibility verdict.

Default operating assumption:
- Toronto is the primary fully specified jurisdiction
- Other Ontario municipalities are allowed, but the output must clearly label Toronto-specific fallbacks and unresolved fields

## Use when

- `source_bundle.json` already exists
- The project needs normalized parcel and policy facts
- A downstream skill needs `normalized_data.json`

## Do not use when

- Official source URLs have not been identified yet
- The task is to compare precedents or assess entitlement risk
- The task is to write the final client-facing report

## Inputs

```json
{
  "project_id": "uuid",
  "source_bundle_path": "source_bundle.json",
  "address_input": "123 Main St, Toronto ON",
  "project_concept": {
    "project_type": "multiplex"
  }
}
```

Required:
- `source_bundle_path`
- One of `address_input` or a parcel identifier present in the source bundle

## Outputs

Produce `normalized_data.json`.

```json
{
  "project_id": "uuid",
  "normalized_timestamp": "ISO datetime",
  "parcel": {},
  "zoning": {},
  "official_plan": {},
  "overlays": [],
  "applications_context": {},
  "unresolved_fields": [],
  "facts": [],
  "inferences": [],
  "assumptions": [],
  "unknowns": [],
  "overall_data_confidence": 0.0
}
```

Use this contract for zoning so downstream skills read consistent paths:

```json
{
  "zoning": {
    "zone_code": "RD",
    "zone_label": "Residential Detached",
    "bylaw_name": "Zoning By-law 569-2013",
    "is_hatched_area": false,
    "legacy_bylaw": null,
    "chapter_900_status": "unverified | not_applicable | confirmed",
    "active_amendment_context": [],
    "development_standards": {
      "max_height_m": 10,
      "max_lot_coverage_pct": 33,
      "fsi": null,
      "min_front_setback_m": 3,
      "min_rear_setback_m": 7.5,
      "min_side_setback_m": 0.9,
      "parking_min_spaces": 1,
      "permitted_uses": [],
      "sources": []
    }
  }
}
```

## Reference Router

Load only the references relevant to the task:

| Topic | Load This Reference |
|-------|--------------------|
| **Provincial override logic** (O.Reg 462/24, housing rules) | `references/ontario-policy-framework.md` |
| **Toronto zone extraction** (569-2013, hatched areas, Chapter 900) | `references/toronto-zoning-guide.md` |
| **Non-Toronto Ontario municipality** | `references/ontario-policy-framework.md` only — Toronto guide does not apply |
| **Both Toronto zoning + provincial override** | Both files |

---

## Workflow

### 1. Resolve the parcel

- Use the best official parcel or address source in `source_bundle.json`
- Resolve address, coordinates, and parcel identifiers first
- If the address cannot be uniquely resolved, stop and return an ambiguity warning instead of guessing

For Toronto:
- Prefer municipal address and parcel sources
- Use geocoding only as a fallback, and label it as such

### 2. Extract zoning facts

- Determine the applicable zone code
- Check for hatched-area or legacy-bylaw conditions
- Extract only the standards needed for feasibility screening:
  - use permissions
  - height
  - lot coverage
  - FSI where applicable
  - setbacks
  - parking

If multiple official sources disagree:
1. Record both
2. State which source is treated as controlling
3. Lower confidence

### 3. Extract Official Plan context

- Resolve the land-use designation
- Check for secondary plans, site-specific policy areas, or similarly material overlays
- Map the designation to compatible and incompatible use categories only when the policy support is explicit

### 4. Extract overlays and application context

Check independently for:
- heritage
- conservation-authority regulation
- flood or hazard mapping
- active planning applications
- recent permits when available

For each overlay entry, record:

```json
{
  "type": "Heritage | TRCA Regulated Area | Floodplain | Active ZBA | Active OPA",
  "applies": true,
  "severity": "low | medium | high | unknown",
  "source_url": "https://...",
  "notes": "Short explanation",
  "confidence": "confirmed | inferred | unknown"
}
```

### 5. Apply Ontario overrides carefully

If the project concept depends on provincial override logic, such as recent Ontario housing rules:
- cite the governing provincial source
- identify exactly which local standard is affected
- record the override as a separate fact, not as a silent replacement

### 6. Normalize for downstream use

- Populate all four reasoning buckets: `facts`, `inferences`, `assumptions`, `unknowns`
- Put every unresolved but material field into `unresolved_fields`
- Keep downstream field paths stable; do not invent ad hoc keys

## Jurisdiction Routing

### Toronto

Run the full workflow using Toronto-specific sources and references.

### Other Ontario municipalities

Run the same output contract, but:
- replace Toronto-specific sources with municipality-specific official sources
- mark Toronto-only checks as not applicable
- surface gaps instead of inventing municipality-specific logic

## Quality Bar

- Every material extracted value must retain a source URL
- Every unresolved material field must be explicit
- Use `development_standards.*` paths consistently for all numeric zoning values
- Do not flatten the zoning contract in one skill and nest it in another

## Stop Conditions

Stop and return a partial artifact when:
- parcel resolution is ambiguous
- the zoning source is blocked or contradictory
- a legacy by-law controls but cannot be retrieved

## Reference Files

| File | Description | Key Topics |
|------|-------------|------------|
| `references/ontario-policy-framework.md` | Provincial hierarchy and override concepts | PPS 2024, O.Reg 462/24, provincial preemption |
| `references/toronto-zoning-guide.md` | Toronto zoning conventions and standard extraction notes | 569-2013 structure, hatched areas, Chapter 900, zone codes |

## External References

| Source | URL | Use |
|--------|-----|-----|
| Provincial Planning Statement, 2024 | https://www.ontario.ca/page/provincial-planning-statement-2024 | Provincial policy hierarchy |
| Toronto Official Plan | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/ | OP designation verification |
| Toronto Zoning By-law 569-2013 | https://www.toronto.ca/zoning/bylaw_amendments/ZBL_NewProvision_Chapter1.htm | By-law text |
| Toronto Zoning Overview | https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/ | Interactive map and zone lookup |
| Heritage Register | https://www.toronto.ca/city-government/planning-development/heritage-preservation/heritage-register/ | Heritage status check |
