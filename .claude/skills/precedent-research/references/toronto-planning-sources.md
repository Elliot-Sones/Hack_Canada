---
title: "Toronto Planning Sources — Precedent Research Reference"
category: precedent-research
relevance: "Load when researching AIC applications, Committee of Adjustment decisions, OLT case search, CanLII tribunal decisions, or building WebSearch queries for precedent cases."
key_topics: "AIC search, CoA decisions, four tests, OLT case search, CanLII, TLAB, OMB, file number formats, radius search, WebSearch patterns"
---

# Toronto Planning Sources — Precedent Research Reference

## Application Information Centre (AIC)

**URL:** https://www.toronto.ca/city-government/planning-development/application-information-centre/

### What It Contains
- All active and historical planning applications: ZBAs, OPAs, Site Plans, Subdivisions
- Committee of Adjustment files: Minor Variances (A-files) and Consents (B-files)
- Uploaded documents: staff reports, drawings, decisions, conditions
- Application status, decision dates, and appeal status

### Navigation
1. Search by address → enter the subject address
2. Select the matching property from the results list
3. View "Applications" tab — shows all files on that property
4. Use the **Radius (meters) filter** to find nearby precedent cases within a specified distance

### Spatial Radius Search (for Precedent Research)
The AIC map search supports a **"Radius (meters)" filter** — enter a specific address and select from:
- **250 metres** — tightest proximity (same block or immediate adjacent)
- **500 metres** — standard precedent search radius
- **1000 metres** — broader neighbourhood context

This is the primary tool for finding comparable nearby cases in the 500-metre radius precedent search.

### File Number Formats
| Type | Format | Example |
|------|--------|---------|
| Minor Variance | A-XXXX/XX | A-0123/23 |
| Consent | B-XXXX/XX | B-0045/23 |
| Zoning By-law Amendment | XX-XXXXXX ZBA | 24-123456 ZBA |
| Official Plan Amendment | XX-XXXXXX OPA | 24-123456 OPA |
| Site Plan | XX-XXXXXX SP | 24-123456 SP |

**Alternative file number format accepted by AIC**: `00 000 00000 AAA 00 AA` or `0000000000AAA00AA`

### Known Limitations
- **Pre-2020 document links are often broken.** Approximately 50/50 chance files from before 2020 are still accessible — document links frequently break. If a document link fails, search the file number via WebSearch: `"[file number]" Toronto planning site:toronto.ca`
- Committee of Adjustment decisions are posted as PDFs — WebFetch can usually read them

---

## Committee of Adjustment (CoA)

**URL:** https://www.toronto.ca/city-government/courts-and-legal-procedures/ontario-municipal-board-toronto-local-appeal-body-tlab/committee-of-adjustment/

### Four District Offices
| District | Coverage | Address |
|---------|---------|---------|
| North York | North York, parts of Scarborough/Etobicoke | 5100 Yonge St |
| Scarborough | Scarborough | 150 Borough Dr |
| Etobicoke York | Etobicoke, York, West Toronto | 399 The West Mall |
| Toronto and East York | Downtown, East York, East Toronto | 100 Queen St W |

### Decision Format
CoA decisions include:
- Application summary
- Staff recommendation (from City Planning)
- Neighbour/community representations
- Four statutory tests applied (minor, appropriate, general intent of ZBL, general intent of OP)
- Decision and conditions imposed

### Decision Appeals
- CoA decisions can be appealed to the **Toronto Local Appeal Body (TLAB)** for minor variances
- TLAB decisions can be appealed to the **Ontario Land Tribunal (OLT)** on points of law
- **URL (TLAB):** https://www.toronto.ca/city-government/courts-and-legal-procedures/ontario-municipal-board-toronto-local-appeal-body-tlab/toronto-local-appeal-body-tlab/

---

## Ontario Land Tribunal (OLT)

**URL:** https://olt.gov.on.ca/

### Case Search
- **Case Search:** https://olt.gov.on.ca/case-search/
- **e-Decisions (for written decisions):** https://olt.gov.on.ca/tribunals/lpat/e-decisions/
- Search by: case number, municipality, address, applicant name, date range
- OLT handles: appeals of ZBAs, OPAs, CoA decisions (via TLAB), expropriation matters

**Active appeal check**: Always search OLT case search for any active appeals on or near the subject property. If an amendment is under active OLT appeal, the legally "in-force" standard remains the pre-amendment standard, not the newly enacted one.

### Decision Format
OLT decisions include:
- Hearing record and participant list
- Issues and positions of parties
- Analysis of OP and ZBL conformity
- Disposition (allowed / dismissed / conditions)

### Pre-2021 (Ontario Municipal Board / TLAB)
The OMB was replaced by the OLT in June 2021.
- OMB decisions: available on **CanLII** at https://www.canlii.org/en/on/onmb/
- TLAB decisions: available on the Toronto TLAB website and CanLII
- For cases from 2021 onwards: OLT decisions are on the OLT website and CanLII

---

## CanLII — Tribunal Decisions

**URL:** https://www.canlii.org/en/on/

### Useful Databases
| Tribunal | CanLII URL |
|---------|-----------|
| Ontario Land Tribunal (OLT) | https://www.canlii.org/en/on/onltb/ |
| Ontario Municipal Board (OMB, historical) | https://www.canlii.org/en/on/onmb/ |
| Toronto Local Appeal Body (TLAB) | https://www.canlii.org/en/on/ontlab/ |

### Search Tips
- Use quotation marks for addresses: `"123 Main Street" Toronto`
- Use zone codes: `"RD zone" "minor variance"`
- Filter by date range for recent decisions
- CanLII full-text search is reliable for decision text; case metadata may be incomplete

---

## Toronto City Council / eSCRIBE

### Council Agendas and Votes
**URL:** https://www.toronto.ca/city-government/council/

For ZBAs and OPAs approved by Council:
1. Search the decision body: Planning and Housing Committee, City Council
2. Filter by date range and committee
3. Staff reports appear as attachments to agenda items

### Clerk's Records
Adopted by-laws (for approved ZBAs) are on the City Clerk's website:
- **URL:** https://www.toronto.ca/city-government/accountability-operations-customer-service/city-administration/city-clerks-office/

---

## WebSearch Patterns for Precedent Research

### Finding Nearby Approvals
```
"[Street Name]" "[Cross Street]" site:toronto.ca planning
"[Street Name]" Committee of Adjustment Toronto minor variance approved
"[Neighbourhood Name]" rezoning Toronto approved site:toronto.ca
```

### Finding Notable Refusals or Contested Cases
```
"[Neighbourhood Name]" OR "[Street Name]" Toronto OLT appeal planning refusal
"[Zone Code]" "refused" "minor variance" Toronto
"[Street Name]" Toronto planning appeal "Ontario Land Tribunal"
```

### Finding OMB/OLT Decisions by Area
```
site:canlii.org "[Neighbourhood Name]" Toronto "zoning by-law amendment"
site:canlii.org "[Street Name]" Toronto "minor variance"
site:canlii.org Toronto "[Zone Code]" "official plan" appeal
```

---

## Reading a Committee of Adjustment Decision

Key sections to extract:

| Section | What to Extract |
|---------|----------------|
| Application | Address, file number, type of variance requested, exact variances (with numbers) |
| Planning Staff Comments | Staff recommendation, which policies cited, staff's assessment of the four tests |
| Representations | Who appeared, neighbourhood association positions, design professional involvement |
| Reasons for Decision | How the panel applied the four tests, conditions imposed |
| Decision | Approved / Refused / Deferred, with exact conditions if approved |

**Four Tests (Minor Variance, Planning Act s.45(1)):**
1. Is it minor in nature?
2. Is it desirable for the appropriate development or use of the land?
3. Does it maintain the general intent and purpose of the Zoning By-law?
4. Does it maintain the general intent and purpose of the Official Plan?

All four tests must be met for approval. A refusal on one test is sufficient grounds to refuse the entire application.
