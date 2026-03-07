---
name: constraints-red-flags
version: "1.0"
description: "Synthesizes upstream feasibility artifacts into a ranked risk and support summary. This skill should be used when the pipeline already has source, normalization, analysis, and precedent outputs and needs a deterministic `constraints_packet.json` for decision support."
source: "Planning Act (Ontario), Provincial Planning Statement 2024, Ontario Building Code (O.Reg 332/12)"
authority: "City of Toronto, Province of Ontario, Ontario Land Tribunal"
data_as_of: "2026-03-07"
pipeline_position: 4
pipeline_inputs: "normalized_data.json, analysis_packet.json, precedent_packet.json, approval_pathway.json"
pipeline_outputs: "constraints_packet.json"
pipeline_upstream: "buildability-analysis, precedent-research, approval-pathway"
pipeline_downstream: "report-generator"
---

# Constraints and Red Flags

## Purpose

Reduce a large artifact set into the few issues that actually change the investment or entitlement decision. This skill is synthesis-only. Do not repeat full research unless an upstream artifact is clearly missing or contradictory.

## Use when

- `normalized_data.json` exists
- `analysis_packet.json` exists
- `precedent_packet.json` or equivalent context exists
- The project needs a ranked risk summary before reporting

## Do not use when

- Upstream extraction is still incomplete
- The task is to discover new sources
- The task is to produce the final memo directly

## Inputs

```json
{
  "project_id": "uuid",
  "normalized_data_path": "normalized_data.json",
  "analysis_packet_path": "analysis_packet.json",
  "precedent_packet_path": "precedent_packet.json",
  "approval_pathway_path": "approval_pathway.json"
}
```

## Outputs

Produce `constraints_packet.json`.

```json
{
  "project_id": "uuid",
  "analysis_timestamp": "ISO datetime",
  "overall_risk_signal": "low | moderate | high | very_high",
  "support_factors": [],
  "barriers": [],
  "legal_ambiguities": [],
  "concern_signals": {
    "planner_concerns": [],
    "community_concerns": [],
    "political_concerns": []
  },
  "critical_gaps": [],
  "facts": [],
  "inferences": [],
  "assumptions": [],
  "unknowns": []
}
```

## Workflow

### 1. Read in priority order

Read artifacts in this order:
1. `analysis_packet.json`
2. `approval_pathway.json` if present
3. `normalized_data.json`
4. `precedent_packet.json`

Use downstream synthesis artifacts first because they already contain filtered decision signals.

### 2. Rank support factors

Include only factors that materially improve the path, such as:
- explicit policy support
- favourable pathway classification
- strong nearby precedent
- absence of high-severity overlays

Limit `support_factors` to the top five by materiality.

### 3. Rank barriers

For each barrier, record:

```json
{
  "barrier": "Heritage designation confirmed",
  "type": "overlay | dimensional | procedural | technical",
  "severity": "minor | moderate | significant | blocking",
  "quantification": "HIA likely required; added process complexity",
  "mitigation_options": ["heritage strategy", "scope redesign"],
  "citation": "artifact or source",
  "confidence": "confirmed | inferred | unknown"
}
```

Limit `barriers` to the top seven by severity and decision impact.

### 4. Isolate true ambiguities

Only create a `legal_ambiguities` entry when:
- two authoritative sources conflict
- the legal status of an amendment or appeal is unclear
- a governing rule cannot be confirmed from public records

Do not use `legal_ambiguities` for ordinary missing data.

### 5. Separate concern signals from hard constraints

Treat these as inferences, not facts:
- planner resistance
- community opposition
- political sensitivity

Each concern signal needs a basis statement.

### 6. Surface decision-changing gaps

Populate `critical_gaps` only with missing information that could flip the conclusion, such as:
- Chapter 900 or site-specific exception status
- title and easements
- servicing capacity
- survey-dependent grades

## Reference Files

| File | Description | Key Topics |
|------|-------------|------------|
| `references/obc-hard-constraints.md` | Ontario Building Code requirements that cannot be varied by Committee of Adjustment | Limiting distances, fire access, WUI, water supply, CoA limits |

## Stop Conditions

Stop and return a partial artifact when:
- Upstream `analysis_packet.json` is missing or has critical unresolved fields
- A legal ambiguity involves an active OLT appeal where outcome is unknown
- More than half of the barrier entries would have `confidence: "unknown"` — the synthesis is not useful

## External References

| Source | URL | Use |
|--------|-----|-----|
| Planning Act, Ontario | https://www.ontario.ca/laws/statute/90p13 | Statutory authority for variances and process |
| Provincial Planning Statement, 2024 | https://www.ontario.ca/page/provincial-planning-statement-2024 | Provincial policy direction |
| Toronto AIC | https://www.toronto.ca/city-government/planning-development/application-information-centre/ | Application history |
| Ontario Land Tribunal | https://olt.gov.on.ca/decisions/ | Tribunal decisions and appeal outcomes |
