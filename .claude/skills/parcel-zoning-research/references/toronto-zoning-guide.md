---
title: "Toronto Zoning By-law 569-2013 — Development Standards Guide"
category: parcel-zoning-research
relevance: "Load when extracting zone codes, development standards, O.Reg 462/24 overrides, Chapter 900 exceptions, or hatched area handling for Toronto parcels."
key_topics: "Zone codes (RD/RS/RT/RM/RA/CR/E), zone map formula, development standards, O.Reg 462/24 multiplex, garden suites, laneway suites, mid-rise CR, Chapter 900, hatched areas, legacy by-laws"
---

# Toronto Zoning By-law 569-2013 — Development Standards Guide

## Zone Code System

Toronto Zoning By-law 569-2013 uses a letter-prefix system with numeric suffixes indicating specific standard sets.

### Residential Zones

| Zone Code | Name | Typical Use | OP Designation |
|-----------|------|-------------|----------------|
| RD | Residential Detached | Single detached dwellings | Neighbourhoods |
| RS | Residential Semi-Detached | Semi-detached dwellings | Neighbourhoods |
| RT | Residential Townhouse | Townhouses, row housing | Neighbourhoods |
| RM | Residential Multiple | Low-rise multiples (3–4 storeys) | Neighbourhoods / Apt. Neigh. |
| RA | Residential Apartment | Apartment buildings | Apartment Neighbourhoods |

### Commercial-Residential Zones

| Zone Code | Name | Typical Use | OP Designation |
|-----------|------|-------------|----------------|
| CR | Commercial Residential | Mixed-use, main streets, avenues | Mixed Use Areas |
| CL | Commercial Local | Neighbourhood commercial nodes | Mixed Use / Neighbourhoods |
| CS | Commercial Services | Auto-oriented commercial | Employment / Mixed Use |

### Employment Zones

| Zone Code | Name |
|-----------|------|
| E | Employment (general) |
| EL | Employment Light |
| EH | Employment Heavy |
| EO | Employment Office |
| EI | Employment Industrial |

### Open Space & Other

| Zone Code | Name |
|-----------|------|
| O | Open Space |
| OR | Open Space Recreation |
| G | Greenbelt |
| GA | Greenbelt Area |
| UA | Utility Area |
| I | Institutional |

---

## Zone Map Formula Notation

Zoning map labels encode site-specific standards using a formula notation:

**Example**: `RD (f12.0; a370; d0.6)` means:
- `f` = minimum lot frontage (12.0m)
- `a` = minimum lot area (370 m²)
- `d` = maximum FSI/Floor Space Index (0.6)

Always read the map label formula for the specific parcel — it overrides the zone defaults below.

---

## Development Standards by Project Type

### Low-Rise Residential (RD, RS, RT Zones)

#### Standard Detached (RD Zone)
| Standard | Typical Value | Notes |
|----------|--------------|-------|
| Min. lot frontage | 7.5m | Varies by RD standard set suffix; read from map label |
| Min. lot depth | 30m | |
| Min. lot area | 225 m² | |
| Max. height | 10m | ~3 storeys; unless specified on Height Overlay Map |
| **Flat roof exception** | **7.2m max, 2 storeys max** | **If roof slope < 1:4 (flat roof), this applies** |
| Max. lot coverage | 33–40% | Dictated by Lot Coverage Overlay Map; no base limit if unmapped |
| Min. front setback | 3m (or prevailing) | Averaging calculation from adjacent buildings within 15m |
| Min. rear setback | 7.5m or 25% of lot depth | Whichever is greater |
| Min. side setback | 0.45–1.2m | Depends on wall height |
| FSI | Typically 0.6x lot area | FSI is **fully removed** for duplexes, triplexes, and fourplexes |

#### Multiplex / Additional Residential Units (O.Reg 462/24 Overrides)

**Applies to**: Lots containing a total of **3 units or fewer** after the addition.

| Standard | Value Under O.Reg 462/24 |
|----------|------------------------|
| Units permitted as-of-right | Up to 4 units (up to 6 in select wards) |
| FSI restriction | **Completely removed** for the lot |
| Lot coverage | **45% maximum** (if local ZBL permits more, the local rule prevails) |
| Max height | Generally 10–12m (3–4 storeys); the greater of 10.0m or map value for multiplexes |
| Min. parking | **0** (Bill 185 removed minimum vehicle parking for multiplexes) |
| Angular plane | **Exempt** — walls can extend straight up to maximum height |
| Separation (ARU) | **4.0m minimum** from primary dwelling (local rule prevails if closer is permitted) |

**Critical limits — O.Reg 462/24 does NOT override:**
- Minimum setbacks (front, rear, side)
- Minimum lot frontage requirements
- Maximum Gross Floor Area (GFA) limits
- Chapter 900 exceptions that restrict frontage, setbacks, or GFA (only lot coverage/FSI/angular plane exceptions are overridden)

---

### Garden Suites & Laneway Suites (ARUs)

| Standard | Garden Suite | Laneway Suite |
|----------|-------------|--------------|
| Max footprint | Smaller of 60 m² or 40% of rear yard area | 8m wide × 10m long absolute (80 m²) |
| Interior floor area | Must be less than primary residence GFA | — |
| Max height | 4.0m default; up to **6.0m if set back ≥7.5m** from main house | 6m (2 storeys) |
| Min. separation from main building | 4m (O.Reg 462/24 minimum) | 4m |
| Min. rear setback | 1.5m from rear lot line | 1.5m from lane |
| Parking | 0 required | 0 required |
| Laneway width requirement | N/A | Abutting public lane required |
| Tree protection | ⚠️ Single protected tree (30cm+ diameter) can legally block construction | Same |
| Fire/emergency access | 1.0m minimum unobstructed path from street; **maximum travel distance 45m** | Same |

**Note**: O.Reg 462/24 prevails over local ZBL restrictions if more permissive. The 4m separation distance is the provincial minimum — local by-law can permit smaller if explicitly stated. Emergency access (1.0m path, 45m max) cannot be varied through Committee of Adjustment — it is an Ontario Building Code requirement.

---

### Mid-Rise Mixed-Use (CR Zones — Avenues)

Height and density in CR zones are tied to the **Right-of-Way (ROW) width** of the abutting street (from the Toronto OP Mid-Rise Guidelines):

| ROW Width | Max Building Height | Approx. Storeys |
|-----------|---------------------|-----------------|
| 20m | 20m | ~6 storeys |
| 23m | 23m | ~7 storeys |
| 27m | 27m | ~8 storeys |
| 30m | 30m | ~9 storeys |
| 36m | 36m | ~11 storeys |

**FSI Ranges in CR Zones:**
| Scenario | FSI Range |
|---------|----------|
| Base CR zone | 4.0–5.0 |
| With rear public lane | 5.0–6.5 |
| Higher-order transit proximity | 6.0–8.2 |

**Key setback and angular plane rules (Mid-Rise):**
- **Front angular plane**: Building must fit within a **45-degree angular plane** measured from the opposite side of the street, initiating at **80% of the ROW width** (e.g., for a 20m ROW: plane starts at 16m height on the opposite side).
- **Rear transition**: Mid-rise buildings must provide rear step-back/angular plane from a **minimum 10.5m (3-storey) base** to protect adjacent low-rise Neighbourhoods.
- **Step-back above streetwall**: Minimum 1.5m step-back required above the streetwall (typically above the 4th–6th storey).
- **Front setback**: Generally 0m (build to the street or setback to match the streetwall).

**Standard Set suffix** (e.g., CR 3.0 (c2.0; r2.5) SS2): The CR code is followed by FSI limits for commercial (c) and residential (r) uses and a Standard Set (SS) number. SS2 is the most common for main street mixed-use.

---

## Chapter 900 — Site-Specific Exceptions

**This is the most critical check in the pipeline.**

Chapter 900 of By-law 569-2013 contains site-specific provisions that override the base zone's development standards for specific properties or small areas. They can:
- Allow uses not normally permitted
- Impose stricter height limits than the base zone
- Grant higher FSI than the base zone
- Restrict uses normally allowed

**How to check:**
1. Resolve the zone code from spatial data.
2. Search the By-law 569-2013 text for the address or nearby streets in Chapter 900.
3. If a Chapter 900 exception exists, it overrides the base zone for that parcel.

**URL for By-law text**: https://www.toronto.ca/zoning/

**Automated check limitation**: There is no machine-readable API for Chapter 900 exceptions. This requires text search or a pre-indexed lookup. **Flag all Chapter 900 checks as requiring confirmation by a human reviewer or a licensed platform (e.g., Zoning Finder).**

---

## Hatched Areas — Legacy By-Laws

If the Toronto zoning map shows a **hatched pattern** over a property, it is governed by a pre-amalgamation by-law (pre-1998), not By-law 569-2013.

Common legacy by-laws by former municipality:
| Former Municipality | Legacy By-law |
|--------------------|--------------|
| City of North York | By-law 7625 |
| City of Etobicoke | By-law 1994-0225 |
| City of Scarborough | By-law 9813 |
| Borough of East York | By-law 6752 |
| City of York | By-law 1-83 |

**Pipeline handling**: If the parcel is in a hatched area:
1. Flag: "Parcel is governed by legacy by-law [number] — 569-2013 development standards do not apply."
2. Attempt to find the legacy by-law on the City of Toronto website or via WebSearch.
3. Mark confidence as "inferred" for all development standards.
4. Recommend human review.

---

## Key Zoning Lookups for Pipeline

### Zoning By-law Full Text
- **URL**: https://www.toronto.ca/zoning/
- **Chapter index available**: Yes — navigate by chapter number

### Toronto Zoning Maps (official PDF maps)
- **URL**: https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-review/zoning-by-law-569-2013-2/

### Interactive Zoning Lookup (most reliable for address-to-zone)
- **URL**: https://map.toronto.ca/maps/map.jsp?app=TorontoMaps_v2
- **Use Playwright MCP if WebFetch fails** (the map is JavaScript-rendered)

### ROW Width Data (for CR zone height calculation)
- **Map 3** of the Toronto Official Plan shows ROW widths
- **Open Data**: https://open.toronto.ca/dataset/centreline/
