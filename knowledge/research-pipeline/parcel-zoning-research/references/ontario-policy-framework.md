---
title: "Ontario Planning Policy Framework"
category: parcel-zoning-research
relevance: "Load when resolving the provincial policy hierarchy, O.Reg 462/24 multiplex overrides, or OP-level designation checks for any Ontario municipality."
key_topics: "Planning Act, PPS 2024, Greenbelt Plan, Official Plan designations, Zoning By-law, Site Plan Control, Bill 23/97/109/185, O.Reg 462/24, FSI, GFA"
---

# Ontario Planning Policy Framework

## Policy Hierarchy (Descending Precedence)

Every municipal planning decision in Ontario must conform to this ladder. Lower documents must be consistent with higher documents. When conflict exists, the higher document prevails.

```
1. Planning Act (R.S.O. 1990, c. P.13)
   ↓ establishes
2. Provincial Policy Statement (PPS, 2024)
   ↓ consistent with
3. Provincial Plans (Greenbelt Plan, Growth Plan remnants)
   ↓ conform to
4. Municipal Official Plan (25-year vision, land use designations)
   ↓ implements
5. Zoning By-law (day-to-day rules: height, density, setbacks, uses)
   ↓ implemented through
6. Site Plan Control (technical layer: street interaction, landscaping, drainage)
```

---

## Level 1: Planning Act

- Supreme provincial framework. Establishes the rules for zoning, appeals, and planning approvals.
- Grants municipalities the right to zone land and set development standards.
- Establishes the Ontario Land Tribunal (OLT) as the appeals body.
- Key sections for pipeline: Section 34 (Zoning By-laws), Section 45 (Minor Variances), Section 41 (Site Plan Control).

## Level 2: Provincial Policy Statement (PPS, 2024)

- Every municipal planning decision "**shall be consistent with**" the PPS.
- Replaced the Growth Plan (Places to Grow) as the single province-wide land use policy document in 2024.
- Key PPS directions relevant to development feasibility:
  - **Housing**: Strong direction to permit and facilitate housing, including a full range of housing types in settlement areas.
  - **Intensification**: Municipalities must plan for intensification of existing built-up areas, particularly around transit.
  - **Natural Heritage**: Development and site alteration are prohibited in significant natural features (wetlands, habitat of endangered species) and must avoid negative impacts on adjacent areas.
  - **Hazard Lands**: Development is not permitted in flood-prone areas without demonstrated risk mitigation.
  - **Employment**: Conversion of designated employment land to non-employment uses requires a municipal comprehensive review (MCR).

## Level 3: Greenbelt Plan

- Geographic-specific mandate that prevails over the PPS in areas of conflict.
- Covers the Greenbelt Area — applies to some Toronto fringe areas (portions of Scarborough, Etobicoke, Rouge Park).
- Development is severely restricted within the Natural Heritage System of the Greenbelt.
- **Pipeline check**: Query the Greenbelt boundary layer. If parcel intersects, flag as "Greenbelt constraint — requires specialist review."

## Level 4: Municipal Official Plan (OP)

Toronto's Official Plan is the constitutional document for land use in Toronto. It:
- Assigns **land use designations** to every parcel (see Toronto Zoning Guide for designation list)
- Sets broad policies for how each designation should develop
- Overrides the Zoning By-law where they conflict (the Zoning By-law must implement the OP)

### Toronto OP Land Use Designations (key ones)

| Designation | Development Intent | Zoning Correlation |
|-------------|------------------|-------------------|
| Neighbourhoods | "Physically stable" low-rise residential. New development must respect and reinforce existing physical character (building types, lot sizes, setbacks). 1-4 storeys. | RD, RS, RT zones |
| Apartment Neighbourhoods | Physically stable areas with taller buildings. Significant city-wide growth not anticipated, but compatible infill (e.g., townhouses on underused surface parking) is permitted if it improves amenities. | RA zones |
| Mixed Use Areas | Absorb majority of anticipated retail, office, service, and housing growth. Ground-floor commercial preferred on main streets. Range of heights from low to mid-rise. Reduces automobile dependency. | CR zones |
| Employment Areas | Divided into Core and General. Exclusively preserved for business and economic activities (manufacturing, warehousing, offices). Conversion to non-employment requires MCR. Very limited residential permitted. | E, EL, EH, EO zones |
| Regeneration Areas | Applied to largely vacant or underused areas. Permits broad mix of commercial, residential, institutional, and light industrial uses to attract investment. | Varies |
| Natural Areas | Environmentally sensitive land. Very limited development. | G, GA zones |
| Parks | Public parks and open space. | G, O zones |
| Utility Corridors | Hydro corridors and utility infrastructure. | UA zones |

**Important**: Toronto OP designation map boundaries **exclude right-of-ways (ROW)**. Zoning boundaries, by contrast, extend to the centreline of the street. For parcels near designation boundaries, always flag for professional confirmation to avoid boundary interpretation errors.

### Secondary Plans & Site and Area Specific Policies (SASPs)
- Many Toronto neighbourhoods have Secondary Plans that overlay the base OP with more detailed policies (e.g., King-Spadina, Yonge-Eglinton, Waterfront). They set tailored urban design frameworks, maximum heights, and densities.
- SASPs (Chapter 7 of the OP) establish unique policy constraints for specific blocks or parcels. **SASPs legally override general OP designations** if there is a conflict — they take precedence over the base designation.
- **Pipeline check**: After resolving OP designation, check if the address falls within a Secondary Plan or SASP boundary. If yes, the SASP/Secondary Plan provisions override the base designation policies.

## Level 5: Zoning By-law

Toronto's primary zoning by-law is **569-2013** (consolidated). It implements the OP through precise numeric standards.

### Key pipeline rules:
1. Resolve the zone code from the spatial data.
2. Look up the zone's development standards (height, FSI, lot coverage, setbacks, parking).
3. **Always check Chapter 900** for site-specific exceptions that override the base zone.
4. **Hatched Areas**: If the parcel is in a hatched area on the zoning map, it is governed by a pre-1998 legacy by-law (e.g., North York By-law 7625, Etobicoke By-law 1994-0225). Flag as "Legacy by-law — standard 569-2013 analysis does not apply."
5. Check **O.Reg 462/24**: For multiplexes and additional residential units, this provincial regulation overrides local ZBL restrictions on lot coverage and FSI if the provincial standard is more permissive.

## Level 6: Site Plan Control

- Technical review layer focusing on building-street interface, landscaping, drainage, servicing.
- **Post-Bill 185 (2024)**: Most residential buildings of **10 units or fewer are EXEMPT** from Site Plan Control, unless located in a "prescribed area":
  - Within 300 metres of a railway corridor
  - Within 120 metres of a wetland
  - Other prescribed areas set by regulation
- Non-residential, commercial, and industrial projects generally still require Site Plan Approval.

---

## Approval Pathway Decision Tree

```
Does the proposal comply with ALL Zoning By-law standards?
├─ YES → Building Permit (as-of-right). Staff approval only.
└─ NO → What kind of non-compliance?
         ├─ Minor deviation from a numeric standard (e.g., slightly too tall, small setback reduction)
         │   → Committee of Adjustment — Minor Variance (4 tests)
         │   Four Tests:
         │     1. Is the variance minor?
         │     2. Is it desirable/appropriate for the land or development?
         │     3. Does it maintain the general intent of the ZBL?
         │     4. Does it maintain the general intent of the OP?
         │
         ├─ Proposed use or density not permitted at all in the zone
         │   → Zoning By-law Amendment (ZBA) — City Council approval required
         │   → If OP designation also needs to change: Official Plan Amendment (OPA) first
         │
         └─ Subdivision/severance of land
             → Consent (Committee of Adjustment) or Plan of Subdivision (Council)
```

---

## Recent Provincial Overrides (Critical for Pipeline)

### O.Reg 462/24 — Additional Residential Units
- Applies to lots containing a total of **3 units or fewer** after the addition.
- Overrides local ZBL restrictions on **lot coverage** (max 45%; higher local limit prevails) and **FSI** (completely removed) if the provincial rule is more permissive.
- Exempts applicable buildings from **angular plane** restrictions.
- Minimum separation: **4.0m** between primary dwelling and ancillary suite (local rule prevails if closer is permitted).
- Allows up to 4 units as-of-right on most residential lots citywide (up to 6 units in specific wards).
- 0 minimum parking required for these units.
- **Prevails over Chapter 900 site-specific exceptions** where those exceptions restrict lot coverage or FSI — but only for those specific standards.
- **Does NOT override**: Minimum setbacks (front, rear, side), minimum lot frontage, maximum GFA.
- **Pipeline logic**: If the base zone code restricts lot coverage below 45% for a multiplex proposal, apply O.Reg 462/24 to check if the provincial standard overrides it. Always separately verify setbacks and frontage against the base zone — they are not overridden.

### Bill 23 / Bill 97 / Bill 109 / Bill 185 — More Homes Built Faster
- **Bill 23**: Removed Site Plan Control for most residential ≤10 units. Also **removed the 2-year prohibition** on applying for minor variances following a site-specific ZBA. **Restricted third-party appeals** of Committee of Adjustment decisions (neighbours can no longer appeal CoA approvals to TLAB as of right).
- **Bill 97**: Further amendments to planning timelines and transition rules.
- **Bill 109**: Imposed **strict mandatory decision timelines** on municipalities for ZBA and OPA applications. Failure to decide within the legislated period triggers a deemed refusal (allowing applicant to appeal) or deemed approval, depending on application type. Also altered community participation and notification requirements.
- **Bill 185**: **Removed minimum vehicle parking spot requirements for multiplexes** citywide. Streamlined Committee of Adjustment timelines further.

---

## Key Terms for the Pipeline

| Term | Definition |
|------|-----------|
| FSI / FAR | Floor Space Index / Floor Area Ratio. Total GFA ÷ Lot Area. Controls density. |
| GFA | Gross Floor Area. All floor area within the building envelope. |
| HT | Height (metres). Measured from established grade. |
| Lot Coverage | Footprint of buildings ÷ Lot Area (%). |
| Setback | Minimum distance from building face to property line. |
| OLT | Ontario Land Tribunal. Hears appeals of planning decisions. |
| ARU | Additional Residential Unit (secondary suite, garden suite, laneway suite). |
| HCD | Heritage Conservation District. Part V designation — design guidelines apply to all buildings. |
| SASP | Site and Area Specific Policy in the Toronto Official Plan. |
| MCR | Municipal Comprehensive Review. Required to convert employment land. |
