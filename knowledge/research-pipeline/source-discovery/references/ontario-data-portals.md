# Ontario Data Portals — Quick Reference

Sources confirmed via NotebookLM knowledge base. Trust levels reflect legal authority, not data freshness.

## Toronto Open Data Quality Scoring (DQS)

Toronto Open Data uses an automated Data Quality Score (DQS) to evaluate dataset reliability. Pipeline should prioritize **Gold** datasets (>80%):

| Factor | Weight |
|--------|--------|
| Freshness | 35% |
| Metadata | 35% |
| Accessibility | 15% |
| Completeness | 10% |
| Usability | 5% |

Datasets scoring below 80% should be flagged for manual verification before relying on them for feasibility determinations.

---

## Parcel & Address Data

### Ontario Parcel (Geospatial Ontario / LIO)
- **URL**: https://ontariogeohub-lio.opendata.arcgis.com
- **Access**: ArcGIS Feature Service API, SHP/GeoJSON/FileGDB download
- **Fields**: Property Identification Number (PIN), Assessment Roll Number (ARN), ownership class, lot/concession boundaries
- **Trust level**: Official
- **Freshness**: Assessment data updates monthly; ownership details require a custom license
- **Notes**: Province-wide standard cadastral layer. Use PIN to cross-reference with OnLand for legal descriptions.

### Toronto Address Points (Toronto Open Data)
- **URL**: https://open.toronto.ca/dataset/address-points-municipal-25k/
- **Access**: WFS/GeoJSON API, daily refresh
- **Fields**: Municipal address, unit number, geographic coordinates (lat/lon), ward
- **Trust level**: Official
- **Freshness**: Refreshed daily
- **Notes**: Required for resolving street addresses to municipal records and coordinates. Use before querying zoning or OP layers.

### OnLand (Ontario Land Registry)
- **URL**: https://www.onland.ca
- **Access**: Web portal — paid per document
- **Fields**: Legal description, registered/unregistered easements, encumbrances, historical title
- **Trust level**: Highest (legal record)
- **Restrictions**: Paid access. Cannot be automated without a licensed API partnership.
- **Notes**: Only source for unregistered utility easements (e.g., Hydro One access rights not visible in GIS). Flag for human review in pipeline — do not attempt automated retrieval.

### MPAC Property Assessment
- **URL**: https://www.mpac.ca / https://about.propertymapping.mpac.ca
- **Access**: Web portal (propertyline.ca for consumers), Assessment Roll for municipalities
- **Fields**: Assessment value, property class, structure type, lot dimensions, year built
- **Trust level**: Semi-official
- **Notes**: Useful for lot frontage and depth if not in open data. Subject to assessment cycle lag.

---

## Zoning Data

### Toronto Zoning By-law 569-2013 (Open Data)
- **URL**: https://open.toronto.ca/dataset/zoning-by-law/
- **CKAN Package ID**: `zoning-by-law`
- **Access**: ArcGIS Feature Service API, GeoJSON download
- **Fields**: Zone code (RD, RS, CR, etc.), max height (HT), floor space index (FSI/d), lot coverage %, setbacks, policy area overlays, rooming house overlays
- **Trust level**: Official — but see reliability warnings below
- **Freshness**: ⚠️ Can lag behind Council-adopted amendments by months
- **Critical warnings**:
  - Does not cover "Hatched Areas" (properties governed by pre-1998 by-laws like North York 7625). Affects ~5–10% of Toronto parcels.
  - OLT appeals: A new height limit may appear in the GIS while the legally in-force limit is the old figure pending appeal outcome.
  - Chapter 900 site-specific exceptions absolutely override base zone mapping. Always check after resolving zone code.

### Toronto Zoning By-law Interactive Map (TSMP)
- **URL**: https://map.toronto.ca/maps/map.jsp?app=TorontoMaps_v2
- **Access**: Interactive browser portal — use Playwright MCP if WebFetch fails
- **Notes**: Most reliable for quick zone label lookup on a specific address. Shows hatched areas visually. Cannot be queried via API.

---

## Official Plan Data

### Toronto Official Plan (City Website)
- **URL**: https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/
- **Access**: PDF consolidations, interactive map
- **Fields**: Land use designations (Neighbourhoods, Mixed Use Areas, Employment Areas, Parks, Utility Corridors, etc.), Secondary Plans, Site and Area Specific Policies (SASPs, Maps 24–34), ROW widths (Map 3)
- **Trust level**: Official — but legal precedence resides in certified Clerk documents
- **Notes**: Map boundaries exclude right-of-ways. For parcels near designation boundaries, always flag for professional confirmation.

### Toronto Official Plan Land Use (Open Data)
- **URL**: https://open.toronto.ca/dataset/official-plan-land-use-designations/
- **Access**: GeoJSON download
- **Notes**: Spatial representation of OP land use. Cross-reference with OP text for policy intent.

---

## Overlay Data

### TRCA Floodline Mapping
- **URL**: https://trca-camaps.opendata.arcgis.com
- **Access**: ArcGIS Feature Service API, GeoJSON
- **Fields**: Regulatory flood line, spill areas, engineered vs. estimated boundary type
- **Trust level**: Official
- **Critical warning**: Boundaries come in two types:
  - **Engineered** (high precision) — reliable for clearance determinations
  - **Estimated** (lower precision) — proximity to estimated lines triggers mandatory physical site survey even if the polygon suggests clearance
- **Notes**: TRCA Regulated Area = provincial jurisdiction. Development within regulated area requires TRCA permit, not just municipal.

### Toronto Heritage Register
- **URL**: https://www.toronto.ca/city-government/planning-development/heritage-preservation/
- **Open Data**: https://open.toronto.ca/dataset/heritage-register/
- **Access**: Interactive heritage search tool (ArcGIS Web App) and Heritage Search Tool, open data download
- **Fields**: Listed vs. Designated status, Heritage Conservation District (HCD) boundaries, property address, designation type (Part IV or Part V Ontario Heritage Act)
- **Trust level**: Official
- **Notes**:
  - **Listed** properties: Trigger 60 days' notice before demolition (City may evaluate for designation). Limited conservation protection but delays demolition.
  - **Designated (Part IV)** properties: A specific Heritage by-law is registered on title detailing the exact "heritage attributes" that must be conserved. Heritage Impact Assessment (HIA) required for any alterations.
  - **HCDs (Part V)**: Design guidelines apply to all buildings within the district, regardless of individual designation status.

### Greenbelt Plan Boundary
- **Access**: Ontario Geohub — search "Greenbelt"
- **Notes**: Primarily relevant for areas outside Toronto proper. Some Toronto fringe areas (Scarborough, Etobicoke) may intersect.

---

## Development & Permit History

### Application Information Centre (AIC)
- **URL**: https://www.toronto.ca/city-government/planning-development/application-information-centre/
- **Access**: Web portal — search by address
- **Fields**: File number, application type, status, decision date, applicant, Committee of Adjustment decisions, architectural drawing links
- **Trust level**: Most authoritative (updates daily)
- **Restrictions**: Links to pre-2020 files are often unstable or broken
- **Notes**: Best source for Committee of Adjustment (minor variance and consent) history. Check before any feasibility assessment — prior variances may expand or restrict current as-of-right permissions.

### Building Permits (Toronto Open Data)
- **URL**: https://open.toronto.ca/dataset/building-permits-active-permits/
- **CKAN Package**: `building-permits-active-permits` and `building-permits-cleared-permits`
- **Access**: JSON/CSV API, daily refresh
- **Fields**: Permit type, address, GFA, units added/removed, status, description of work
- **Trust level**: Official (updates daily)
- **Notes**: Reveals recent densification on or near the parcel. Multiple permit applications on a lot may indicate an owner already pursuing development.

### Development Applications (Toronto Open Data)
- **URL**: https://open.toronto.ca/dataset/development-applications/
- **Access**: JSON/CSV API
- **Fields**: Application type (OPA, ZBA, Site Plan, Subdivision), address, status, ward
- **Trust level**: Official
- **Notes**: Shows active or recently decided zoning amendments, official plan amendments, and site plan applications. An active ZBA on a parcel means the base zoning is contested — flag as requires human review.

---

## Environmental & Infrastructure Overlays

### Toronto Tree Protection (Urban Forestry)
- **URL**: https://www.toronto.ca/city-government/accountability-operations-customer-service/long-term-vision-plans-and-strategies/toronto-urban-forest-strategic-plan/
- **Notes**: A single protected tree (30cm+ diameter or city-designated heritage tree) can legally block an otherwise as-of-right garden suite. No centralized open data layer for tree locations — flag all rear-yard development for urban forestry review.

### Toronto Hydro Load Capacity
- **URL**: Via Toronto Hydro customer service / capacity maps (updated quarterly)
- **Notes**: Uses a **Green/Yellow/Red** traffic-light model — green = high available capacity, red = high likelihood of expensive infrastructure upgrades or severe constraints. Maps explicitly state they do not replace engineering studies. Flag high-density proposals (10+ units) for hydro capacity check.

---

## Source Reliability Summary

| Source | Trust | Freshness | Primary Use |
|--------|-------|-----------|-------------|
| OnLand (title) | ★★★★★ | Real-time | Legal description, easements |
| AIC / Building Permits API | ★★★★★ | Daily | Permit & application history |
| Ontario Parcel (LIO) | ★★★★☆ | Monthly | Parcel boundaries, PIN |
| TRCA Floodline (Engineered) | ★★★★☆ | Annual | Flood constraint |
| Toronto Zoning 569-2013 (Open Data) | ★★★☆☆ | Months lag | Zone code — verify against Chapter 900 |
| Toronto OP Open Data | ★★★☆☆ | Months lag | Designation — verify against Clerk's copy |
| MPAC | ★★★☆☆ | Assessment cycle | Lot dimensions, property class |
| TRCA Floodline (Estimated) | ★★☆☆☆ | — | Trigger for site survey, not clearance |
