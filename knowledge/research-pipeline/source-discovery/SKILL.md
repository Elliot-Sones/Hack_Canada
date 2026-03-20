---
name: source-discovery
version: "1.0"
description: "Discovers official public-source entry points for Ontario site-feasibility research. This skill should be used when a project starts with an address, parcel identifier, or municipality and the pipeline needs a `source_bundle.json` of official datasets, maps, portals, and fallback sources before extraction begins."
source: "Toronto Open Data, Ontario Geohub (LIO), City of Toronto Official Plan, TRCA, AIC"
authority: "City of Toronto, Province of Ontario, TRCA"
data_as_of: "2026-03-07"
pipeline_position: 1
pipeline_outputs: "source_bundle.json"
pipeline_downstream: "parcel-zoning-research"
---

# Source Discovery

## Purpose

Discover the minimum viable set of official sources needed to research a site. Stop at source identification and source classification. Do not extract parcel facts, zoning standards, or planning conclusions here.

Keep this skill narrow:
- Find official URLs
- Rank source authority
- Record access issues and fallback routes
- Hand off to `parcel-zoning-research`

## Use when

- A new site-feasibility project has started
- The project has an address, parcel ID, or municipality but no trusted source inventory
- An upstream agent needs a `source_bundle.json`

## Do not use when

- Zoning, Official Plan, or overlay facts have already been extracted
- The task is to interpret policy, assess feasibility, or write the final report
- The task is Toronto-only zoning extraction from known datasets; route that to `parcel-zoning-research`

## Inputs

```json
{
  "project_id": "uuid",
  "jurisdiction": "Toronto",
  "address_input": "123 Main St, Toronto ON",
  "parcel_id": null,
  "project_type": "multiplex",
  "research_scope": "core | expanded"
}
```

Required fields:
- `jurisdiction`
- One of `address_input` or `parcel_id`

Optional fields:
- `project_type`
- `research_scope`

## Outputs

Produce exactly one artifact: `source_bundle.json`.

```json
{
  "project_id": "uuid",
  "jurisdiction": "Toronto",
  "address_input": "123 Main St, Toronto ON",
  "discovery_timestamp": "ISO datetime",
  "sources": {
    "parcel_lookup": [],
    "zoning": [],
    "official_plan": [],
    "overlays": [],
    "applications_and_precedents": [],
    "supplementary": []
  },
  "not_found": [],
  "access_notes": [],
  "recommended_next_skill": "parcel-zoning-research"
}
```

Each source entry must include:

```json
{
  "name": "Toronto Open Data Portal",
  "url": "https://open.toronto.ca/",
  "source_type": "open_data | bylaw_text | official_plan | application_portal | conservation_authority | registry | map",
  "authority": "official | quasi_official | secondary",
  "coverage": "parcel | zoning | official_plan | heritage | flood | applications | permits",
  "access_method": "direct_download | html_page | interactive_map | search_portal",
  "status": "confirmed | likely | blocked",
  "notes": "Short operational note"
}
```

## Reference Router

Load only the reference file relevant to the current municipality:

| Municipality | Load This Reference |
|-------------|--------------------|
| **Toronto** | `references/toronto-open-data.md` |
| **Any Ontario municipality** | `references/ontario-data-portals.md` |
| **Toronto + need portal patterns** | Both files — `ontario-data-portals.md` for trust levels and source hierarchy, `toronto-open-data.md` for API endpoints |

---

## Workflow

### 1. Scope the jurisdiction

- Confirm municipality and province from the input
- Default Ontario projects to the Ontario/Toronto research stack unless the user specifies another province
- If the municipality is outside Ontario, stop and return a scoped failure rather than improvising

### 2. Find the core official sources

Always try to identify these categories:
- Parcel or address lookup
- Zoning map or zoning dataset
- Zoning by-law text
- Official Plan page or land-use map
- Heritage register
- Conservation-authority or hazard mapping
- Planning application history

For Toronto, prefer the official public stack in this order:
1. City of Toronto Open Data portal
2. City of Toronto Official Plan pages
3. Zoning By-law 569-2013 pages and interactive zoning resources
4. Application Information Centre
5. TRCA regulated-area mapping

### 3. Classify each source

For every discovered source, record:
- Authority level
- Access method
- Expected downstream use
- Whether extraction is likely direct or requires portal fallback

Prefer official machine-readable datasets over PDFs and interactive maps. Prefer official HTML pages over third-party summaries.

### 4. Record missing or blocked categories

- Put every missing category in `not_found`
- Put every interactive-only or brittle source in `access_notes`
- Recommend the exact downstream fallback, for example: `interactive map`, `manual lookup`, or `browser automation`

### 5. Hand off cleanly

Return only source metadata. Do not:
- Geocode
- Extract parcel geometry
- Pull zoning standards
- Infer policy compatibility
- Write feasibility conclusions

The handoff contract is:
- `source-discovery` produces `source_bundle.json`
- `parcel-zoning-research` consumes `source_bundle.json` and produces `normalized_data.json`

## Quality Bar

- Include at least one official source for zoning, Official Plan, and overlays when available
- Prefer sources with stable URLs over search-result URLs
- Mark uncertain availability as `likely`, not `confirmed`
- Never fabricate a dataset slug, API URL, or portal endpoint

## Stop Conditions

Stop and return a scoped warning when:
- The municipality cannot be identified confidently
- Only secondary sources are discoverable
- The official source exists but blocks access and no fallback path is visible

## Reference Files

| File | Description | Key Topics |
|------|-------------|------------|
| `references/ontario-data-portals.md` | Ontario municipal portal patterns, trust levels, source hierarchy | Toronto Open Data DQS, OnLand, MPAC, TRCA, Heritage Register, AIC, building permits |
| `references/toronto-open-data.md` | Toronto CKAN API endpoints, spatial query patterns, geocoding | Package IDs, GeoJSON endpoints, point-in-polygon, data freshness checks |

Read only the reference file relevant to the current municipality.

## External References

| Source | URL | Use |
|--------|-----|-----|
| Toronto Open Data Portal | https://open.toronto.ca/ | Primary dataset discovery |
| Toronto Official Plan | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/ | OP designation lookup |
| Toronto Zoning By-laws | https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/ | Zone code verification |
| Toronto AIC | https://www.toronto.ca/city-government/planning-development/application-information-centre/ | Application history |
| TRCA Mapping Guidance | https://trca.ca/regulation-mapping-update/ | Regulated area boundaries |
