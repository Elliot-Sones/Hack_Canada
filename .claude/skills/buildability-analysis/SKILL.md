---
name: buildability-analysis
version: "1.0"
description: "Evaluates a proposed project concept against normalized Ontario parcel, zoning, Official Plan, and overlay data. This skill should be used when `normalized_data.json` and a project concept are available and the pipeline needs an `analysis_packet.json` with verdict, pathway signal, planning-context summary, and explicit facts, inferences, assumptions, and unknowns."
source: "Toronto Zoning By-law 569-2013, Toronto Official Plan, O.Reg 462/24, Ontario Building Code"
authority: "City of Toronto, Province of Ontario"
data_as_of: "2026-03-07"
pipeline_position: 3
pipeline_inputs: "normalized_data.json"
pipeline_outputs: "analysis_packet.json"
pipeline_upstream: "parcel-zoning-research"
pipeline_downstream: "constraints-red-flags, approval-pathway, report-generator"
---

# Buildability Analysis

## Purpose

Turn normalized policy facts into a conservative feasibility assessment. Use only the fields already extracted into `normalized_data.json` plus narrowly scoped planning-context research where required. Do not restate the entire source record.

## Use when

- `normalized_data.json` exists
- The project concept is defined well enough to compare against policy controls
- The next step needs an `analysis_packet.json`

## Do not use when

- Parcel or zoning facts are still unresolved
- The task is to discover sources or extract raw by-law text
- The task is to write the final human-facing report

## Inputs

```json
{
  "project_id": "uuid",
  "normalized_data_path": "normalized_data.json",
  "project_concept": {
    "project_type": "multiplex",
    "proposed_units": 4,
    "proposed_height_m": 10,
    "proposed_gfa_m2": 320,
    "proposed_lot_coverage_pct": 45
  }
}
```

## Outputs

Produce `analysis_packet.json`.

```json
{
  "project_id": "uuid",
  "analysis_timestamp": "ISO datetime",
  "project_concept": {},
  "feasibility_verdict": "green | yellow | red | unknown",
  "approval_signal": "as_of_right | by_right_with_site_plan | minor_variance | rezoning | opa_rezoning | cannot_determine",
  "overall_confidence": 0.0,
  "findings": {
    "use_permissions": {},
    "development_standards": [],
    "overlays": [],
    "planning_context": {}
  },
  "opportunities": [],
  "blockers": [],
  "items_requiring_human_review": [],
  "facts": [],
  "inferences": [],
  "assumptions": [],
  "unknowns": [],
  "confidence_deductions": []
}
```

## Reference Router

Load the reference only when the analysis reaches the relevant stage:

| Analysis Stage | Load This Reference |
|---------------|--------------------|
| **Dimensional compliance + overlay checks** (Stages 2–5) | `references/analysis-framework.md` |
| **O.Reg 462/24 multiplex override** (Stage 5 only) | `references/analysis-framework.md` — Stage 5 section |
| **Ontario Building Code hard constraints** | See `constraints-red-flags` skill — `references/obc-hard-constraints.md` |

---

## Workflow

### 1. Validate the inputs

- Confirm parcel geometry and zoning resolution are usable
- Confirm the project concept is specific enough for dimensional checks
- If critical dimensions are missing, continue only with use-permission and high-level policy analysis; mark standards as unknown

### 2. Check use permissions

Read from these normalized paths:
- `zoning.development_standards.permitted_uses`
- `official_plan.compatible_uses`
- `official_plan.incompatible_uses`

Classify the proposed use as:
- `as_of_right`
- `minor_variance`
- `rezoning`
- `opa_rezoning`
- `cannot_determine`

Do not infer by-right status when either zoning applicability or Official Plan compatibility is unresolved.

### 3. Check development standards

Read all dimensional controls from `zoning.development_standards.*`.

For each standard, produce:

```json
{
  "standard": "height",
  "permitted_value": "10 m",
  "proposed_value": "9.5 m",
  "status": "compliant | minor_variance_needed | major_relief_needed | unknown",
  "confidence": 0.0,
  "source_urls": []
}
```

If a provincial override changes the local rule:
- keep the local rule visible
- record the override explicitly
- explain why the override is treated as controlling

### 4. Assess overlays

Use overlay `severity` from `normalized_data.json` where available.

If an upstream overlay lacks severity:
- assign one in analysis as an inference
- explain the reasoning

Treat high-severity overlays as blockers until evidence supports a lower impact.

### 5. Add planning-context research only where it matters

Research planning intent only when it could change the feasibility conclusion, such as:
- growth-area targeting
- secondary-plan support or conflict
- heritage or hazard policy direction
- major application activity nearby

Use official sources first. Keep this section short and decision-relevant.

### 6. Surface human-review items

Always consider whether these remain unresolved:
- title and easements
- servicing capacity
- tree protection
- established grade and survey-dependent measurements
- environmental contamination

Do not clear these items without evidence.

### 7. Score confidence

Start at `1.0`, then deduct for unresolved or unstable conditions such as:
- stale source data
- hatched or legacy zoning
- active amendments or appeals
- blocked source retrieval
- material parcel ambiguity

Record every deduction in `confidence_deductions`.

## Decision Rules

- `green`: use permitted, no known major dimensional conflict, no high-severity blocker confirmed
- `yellow`: viable but process-heavy or materially uncertain
- `red`: use prohibited, major relief clearly required, or a high-severity blocker is confirmed
- `unknown`: too many unresolved controls to support a reliable verdict

## Quality Bar

- Use the normalized contract exactly; do not switch to flattened zoning paths
- Keep the analysis decision-oriented, not source-dump oriented
- Every blocker and opportunity must point back to an extracted fact or an explicit inference

## Reference Files

| File | Description | Key Topics |
|------|-------------|------------|
| `references/analysis-framework.md` | Detailed checklist for physical and procedural constraints | Parcel ID, zoning classification, OP designation, overlays, O.Reg 462/24, confidence scoring, feasibility verdicts |

Read only the sections needed for the project type and jurisdiction.

## Stop Conditions

Stop and return a partial artifact when:
- Parcel geometry or zoning resolution is unusable
- The project concept is too vague for dimensional checks
- `normalized_data.json` has critical unresolved fields that would flip the verdict
- An active OLT appeal makes the controlling zoning standard indeterminate

## External References

| Source | URL | Use |
|--------|-----|-----|
| Provincial Planning Statement, 2024 | https://www.ontario.ca/page/provincial-planning-statement-2024 | Provincial override logic |
| Toronto Official Plan | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/ | OP compatibility check |
| Toronto Official Plan Chapter 2 | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/chapters-1-5/official-plan-chapter-2-shaping-the-city/ | Growth area and secondary plan policy |
| Toronto Zoning Overview | https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/ | Zone code verification |
| TRCA Mapping Guidance | https://trca.ca/regulation-mapping-update/ | Regulated area constraint |
