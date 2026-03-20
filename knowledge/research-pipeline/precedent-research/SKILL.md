---
name: precedent-research
version: "1.0"
description: "Researches nearby and comparable planning cases for Ontario site-feasibility. This skill should be used when `normalized_data.json` exists and the pipeline needs a `precedent_packet.json` of relevant decisions, approvals, refusals, and OLT outcomes."
source: "Toronto AIC, Ontario Land Tribunal, Toronto Building Permits API"
authority: "City of Toronto, Ontario Land Tribunal"
data_as_of: "2026-03-07"
pipeline_position: 3
pipeline_inputs: "normalized_data.json"
pipeline_outputs: "precedent_packet.json"
pipeline_upstream: "parcel-zoning-research"
pipeline_downstream: "approval-pathway, constraints-red-flags, report-generator"
---

# Precedent Research

## Purpose

Find relevant planning history without overstating what precedent can prove. Prioritize nearby official case history first, then expand to comparable cases and tribunal decisions.

## Use when

- The subject site and project concept are known
- The pipeline needs precedent signals for entitlement-risk analysis
- Nearby approvals, refusals, or appeals could change the recommendation

## Do not use when

- The task is to discover baseline parcel or zoning sources
- The task is to extract current zoning standards
- The task is to write the final report without supporting case research

## Inputs

```json
{
  "project_id": "uuid",
  "subject_address": "123 Main St, Toronto ON",
  "municipality": "Toronto",
  "project_concept": {
    "project_type": "multiplex"
  },
  "search_radius_m": 500
}
```

## Outputs

Produce `precedent_packet.json`.

## Workflow

### 1. Search nearby official application history first

For Toronto, prioritize:
- Application Information Centre
- official staff reports
- official committee or tribunal records linked from the application record

Start with the subject site, then the immediate surrounding area.

### 2. Expand to comparable cases only when needed

If nearby history is thin or not directly comparable:
- search for the same relief type
- search for the same zone or land-use context
- search for recent tribunal decisions that clarify the issue

### 3. Treat case status carefully

Allowed outcome labels:
- approved
- refused
- withdrawn
- under_appeal
- pending
- unknown

Do not call an application approved because it was filed, discussed, or recommended.

### 4. Produce a structured case record

For each case, record:

```json
{
  "case_id": "AIC or tribunal identifier",
  "address": "123 Main St",
  "distance_from_subject_m": 0,
  "application_type": "Minor Variance | ZBA | OPA | Site Plan | Appeal",
  "status": "approved | refused | withdrawn | under_appeal | pending | unknown",
  "project_description": "",
  "relief_sought": "",
  "decision_date": null,
  "decision_summary": "",
  "source_url": "",
  "confidence": "confirmed | inferred | unknown",
  "relevance_to_subject": ""
}
```

### 5. Synthesize cautiously

Summarize:
- what relief types appear common
- what refusal reasons repeat
- whether the area shows favourable, mixed, or unfavourable precedent

Do not convert precedent into a probability score unless the evidence is unusually strong and recent.

## Fallback Rules

- If the official application portal is incomplete, search by file number or address through official records or CanLII
- If case status cannot be confirmed, keep the case but mark the outcome unknown
- If no reliable precedent exists, return `insufficient_data`

## Reference Files

| File | Description | Key Topics |
|------|-------------|------------|
| `references/toronto-planning-sources.md` | Toronto AIC, staff-report, and tribunal search guidance | AIC, staff reports, tribunal records |
| `references/olt-search-patterns.md` | OLT case search strategies and result interpretation | Search queries, case classification, decision weight |

## Stop Conditions

Stop and return a partial artifact when:
- No applications or decisions are found within a 500m radius or comparable scope
- AIC search results are ambiguous and cannot be classified with confidence
- The OLT case database is unreachable or returns incomplete results
- The parcel's zone or OP designation is unresolved (precedent relevance depends on these)

## Quality Bar

- State the evidence, not the conclusion — no predictions from precedent
- Categorize cautiously: "approved" means approved, not "likely approved"
- Never call precedent "binding" — distinguish precedent from binding case law

## External References

| Source | URL | Use |
|--------|-----|-----|
| Toronto AIC | https://www.toronto.ca/city-government/planning-development/application-information-centre/ | Application and CoA decision history |
| City of Toronto Committee of Adjustment | https://www.toronto.ca/city-government/planning-development/committee-of-adjustment/ | Committee of Adjustment decisions |
| Ontario Land Tribunal | https://olt.gov.on.ca/decisions/ | Tribunal decisions and appeals |
| Toronto Dev Applications (Open Data) | https://open.toronto.ca/dataset/development-applications/ | Active ZBAs, OPAs, site plans |
| Toronto Building Permits (Open Data) | https://open.toronto.ca/dataset/building-permits-active-permits/ | Recent permit activity |
| CanLII Ontario Land Tribunal collection | https://www.canlii.org/en/on/onltb/ | Legal research for OLT cases |

