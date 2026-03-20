---
name: approval-pathway
version: "1.0"
description: "Determines the likely entitlement pathway for an Ontario development concept from existing feasibility artifacts. This skill should be used when normalized zoning and analysis outputs exist and the pipeline needs an `approval_pathway.json` that classifies process route, major dependencies, and uncertainty."
source: "Planning Act (Ontario), City of Toronto Committee of Adjustment, OLT"
authority: "Province of Ontario, City of Toronto"
data_as_of: "2026-03-07"
pipeline_position: 5
pipeline_inputs: "normalized_data.json, analysis_packet.json, precedent_packet.json"
pipeline_outputs: "approval_pathway.json"
pipeline_upstream: "buildability-analysis, precedent-research"
pipeline_downstream: "constraints-red-flags, report-generator"
---

# Approval Pathway

## Purpose

Classify the most likely process route for the proposed concept. Keep the output conservative and explicit about uncertainty. This skill is downstream of extraction and analysis; it does not perform primary source discovery.

## Use when

- `normalized_data.json` exists
- `analysis_packet.json` exists
- The project needs a process-path classification and timeline signal

## Do not use when

- Zoning or Official Plan applicability is still unresolved
- The task is to evaluate design feasibility from scratch
- The task is to write the final client-facing report

## Inputs

```json
{
  "project_id": "uuid",
  "normalized_data_path": "normalized_data.json",
  "analysis_packet_path": "analysis_packet.json",
  "precedent_packet_path": "precedent_packet.json"
}
```

`precedent_packet.json` is optional but recommended for minor-variance risk assessment.

## Outputs

Produce `approval_pathway.json`.

```json
{
  "project_id": "uuid",
  "pathway_timestamp": "ISO datetime",
  "primary_pathway": "by_right | by_right_with_site_plan | minor_variance | minor_variance_with_site_plan | rezoning | opa_rezoning | cannot_determine",
  "pathway_confidence": "confirmed | inferred | unknown",
  "site_plan_required": false,
  "variances_required": [],
  "external_approvals": [],
  "estimated_timeline": {},
  "major_dependencies": [],
  "facts": [],
  "inferences": [],
  "assumptions": [],
  "unknowns": []
}
```

## Workflow

### 1. Confirm the controlling policy posture

- Read use permission and dimensional results from `analysis_packet.json`
- Confirm whether the controlling issue is:
  - no relief
  - minor variance
  - rezoning
  - Official Plan amendment plus rezoning
  - unresolved applicability

If either zoning applicability or Official Plan compatibility is materially uncertain, return `cannot_determine`.

### 2. Decide whether site plan control is additive

Treat site plan as an additional process flag, not an ambiguous substitute for pathway classification. If site plan applies, encode it through:
- `site_plan_required`
- `primary_pathway` values that explicitly include site plan when it is central to the route

### 3. Assess variance risk when variance is the likely path

For each variance candidate:
- quantify the gap
- identify the controlling standard
- classify it as low, medium, or high risk
- use nearby or comparable precedents only as support signals, not as substitutes for the statutory test

### 4. Identify parallel dependencies

Check for process dependencies such as:
- conservation-authority approvals
- heritage review
- servicing or engineering submissions
- tree-protection approvals

Only include dependencies that are supported by an upstream fact or a clearly labeled inference.

### 5. Estimate the timeline conservatively

Provide:
- optimistic
- likely
- conservative

Each timeline must include a short basis statement.

## Decision Rules

- `by_right`: no known planning relief required
- `by_right_with_site_plan`: compliant but site plan or comparable administrative review is still required
- `minor_variance`: numeric or limited standards relief appears required
- `minor_variance_with_site_plan`: both variance and site plan are likely required
- `rezoning`: zoning change appears required
- `opa_rezoning`: Official Plan conflict plus rezoning required
- `cannot_determine`: unresolved controls make the route unreliable

## Quality Bar

- Keep the enum and the decision table aligned
- Never hide uncertainty inside a seemingly precise pathway label
- Use `site_plan_required` in addition to, not instead of, the primary pathway

## Stop Conditions

Stop and return `cannot_determine` when:
- Either zoning applicability or Official Plan compatibility is materially uncertain
- `analysis_packet.json` is missing or has unresolved critical findings
- An active OLT appeal on the parcel makes the controlling standard indeterminate

## External References

| Source | URL | Use |
|--------|-----|-----|
| Planning Act, Ontario | https://www.ontario.ca/laws/statute/90p13 | Statutory process definitions |
| Ontario e-Laws Regulations | https://www.ontario.ca/laws/regulations | Regulation lookups |
| Toronto Committee of Adjustment | https://www.toronto.ca/city-government/planning-development/committee-of-adjustment/ | Variance process and decisions |
| Toronto Development Applications | https://www.toronto.ca/city-government/planning-development/development-applications-guidelines/ | Application guides and forms |
