---
name: report-generator
version: "1.0"
description: "Assembles upstream feasibility artifacts into a client-facing report in JSON and Markdown formats. This skill should be used when the pipeline has all or most of: analysis_packet.json, precedent_packet.json, constraints_packet.json, approval_pathway.json."
source: "Assembled from pipeline outputs — no primary source authority"
authority: "N/A — synthesis skill"
data_as_of: "2026-03-07"
pipeline_position: 6
pipeline_inputs: "normalized_data.json, analysis_packet.json, precedent_packet.json, constraints_packet.json, approval_pathway.json"
pipeline_outputs: "final_report.json, final_report.md"
pipeline_upstream: "all prior pipeline skills"
pipeline_downstream: "none — terminal skill"
---

# Report Generator

## Purpose

Assemble a readable, auditable report from existing artifacts. Preserve uncertainty. Do not introduce new legal or planning conclusions that are not already supported upstream.

## Use when

- `analysis_packet.json` exists
- The project needs a final report for human review or UI display
- Upstream artifacts are stable enough to cite

## Do not use when

- Source discovery or extraction is still incomplete
- Major analysis questions are still unresolved
- The task is to do new research rather than present existing findings

## Inputs

```json
{
  "project_id": "uuid",
  "source_bundle_path": "source_bundle.json",
  "normalized_data_path": "normalized_data.json",
  "analysis_packet_path": "analysis_packet.json",
  "report_format": "json_and_markdown"
}
```

Optional supporting inputs:
- `precedent_packet.json`
- `constraints_packet.json`
- `approval_pathway.json`

If optional artifacts are missing, omit those sections cleanly rather than inventing placeholders.

## Outputs

Produce:
- `final_report.json`
- `final_report.md`

## Assembly Order

### 1. Establish the executive summary

Build this section only from the strongest supported upstream findings:
- verdict
- pathway signal
- overall confidence
- top opportunities and blockers

Never promote an inference into a fact in the summary.

### 2. Build the site and policy snapshot

Use `normalized_data.json` for:
- address and parcel summary
- zoning
- Official Plan
- overlays

Keep this section factual and compact.

### 3. Build the compliance and findings sections

Use `analysis_packet.json` for:
- dimensional comparisons
- blockers
- opportunities
- human-review items
- reasoning buckets

When a claim appears in markdown, make sure the same source or artifact appears in the source appendix.

### 4. Handle partial or conflicting data

- Drop sections that cannot be supported
- Replace missing sections with short explicit notes such as `Not determined from available public sources`
- Explain conflicts instead of smoothing them over

### 5. Finalize the appendix and disclaimer

Append:
- source appendix
- confidence notes
- mandatory disclaimer

## Output Contract

Use this report shape:

```json
{
  "project_id": "uuid",
  "report_timestamp": "ISO datetime",
  "executive_summary": {},
  "site_summary": {},
  "policy_snapshot": [],
  "compliance_table": [],
  "findings_by_category": {
    "facts": [],
    "inferences": [],
    "assumptions": [],
    "unknowns": []
  },
  "opportunities": [],
  "blockers": [],
  "items_requiring_human_review": [],
  "next_steps": [],
  "source_appendix": [],
  "disclaimer": ""
}
```

## Writing Rules

- Prefer plain English over planner jargon when both are possible
- Keep the distinction between facts, inferences, assumptions, and unknowns visible
- Keep the tone analytical, not promotional
- Cite authoritative sources and source artifacts for every material claim

## Do NOT

- Invent findings not present in upstream artifacts
- Interpret or recommend — report only
- Omit the mandatory disclaimer
- Mix up sources between pipeline artifacts

## Stop Conditions

Stop and return a partial report when:
- `analysis_packet.json` is missing — this is the core artifact
- Upstream artifacts have contradictory verdicts that cannot be editorially reconciled
- More than 2 of the 5 expected input artifacts are missing for every material claim

## Quality Bar

- A reviewer should be able to trace every major claim back to a source or upstream artifact
- Empty sections should be dropped or explicitly marked unavailable
- The markdown memo and JSON output must tell the same story

## Mandatory Disclaimer

Append this disclaimer, updated with the report date:

> This report is a preliminary feasibility screening based on publicly available information and the listed source artifacts. It is not legal, planning, architectural, engineering, or surveying advice. Public records may lag legislative change, appeal outcomes, or unpublished site conditions. Human professional review is required before any acquisition, entitlement, or design decision.

## External References

| Source | URL | Use |
|--------|-----|-----|
| Toronto Official Plan | https://www.toronto.ca/city-government/planning-development/official-plan-guidelines/official-plan/ | Citation in report |
| Toronto Zoning Overview | https://www.toronto.ca/city-government/planning-development/zoning-by-law-preliminary-zoning-reviews/ | Citation in report |
| Ontario Land Tribunal | https://olt.gov.on.ca/decisions/ | Tribunal case citation |
| Planning Act, Ontario | https://www.ontario.ca/laws/statute/90p13 | Statutory citation |
