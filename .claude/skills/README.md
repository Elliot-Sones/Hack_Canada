# Site-Feasibility Pipeline — Skills Index

Skills directory for the Ontario site-feasibility pipeline. Each skill produces a JSON artifact consumed by downstream skills.

## Pipeline Order

```
Address / Parcel Input
       │
       ▼
  ┌─────────────────────┐
  │  source-discovery    │ → source_bundle.json
  │  (Phase 1)           │
  └────────┬────────────┘
           ▼
  ┌─────────────────────┐
  │  parcel-zoning-      │ → normalized_data.json
  │  research (Phase 2)  │
  └────────┬────────────┘
           ├──────────────────┐
           ▼                  ▼
  ┌────────────────┐  ┌────────────────┐
  │  buildability-  │  │  precedent-    │ → precedent_packet.json
  │  analysis       │  │  research      │
  │  (Phase 3)      │  │  (Phase 3b)    │
  └────────┬───────┘  └────────┬───────┘
           │                   │
           ▼                   ▼
  ┌─────────────────────┐  ┌─────────────────────┐
  │  constraints-        │  │  approval-pathway    │ → approval_pathway.json
  │  red-flags (Phase 4) │  │  (Phase 5)           │
  └────────┬────────────┘  └────────┬────────────┘
           │                        │
           └───────────┬────────────┘
                       ▼
           ┌─────────────────────┐
           │  report-generator    │ → final_report.json
           │  (Phase 6)           │    final_report.md
           └─────────────────────┘
```

## Skill Inventory

| # | Skill | Input | Output | References |
|---|-------|-------|--------|------------|
| 1 | [source-discovery](source-discovery/SKILL.md) | Address / municipality | `source_bundle.json` | 2 |
| 2 | [parcel-zoning-research](parcel-zoning-research/SKILL.md) | `source_bundle.json` | `normalized_data.json` | 2 |
| 3 | [buildability-analysis](buildability-analysis/SKILL.md) | `normalized_data.json` | `analysis_packet.json` | 1 |
| 3b | [precedent-research](precedent-research/SKILL.md) | `normalized_data.json` | `precedent_packet.json` | 1 |
| 4 | [constraints-red-flags](constraints-red-flags/SKILL.md) | All upstream artifacts | `constraints_packet.json` | 1 |
| 5 | [approval-pathway](approval-pathway/SKILL.md) | Analysis + precedent | `approval_pathway.json` | 0 |
| 6 | [report-generator](report-generator/SKILL.md) | All upstream artifacts | `final_report.json` + `.md` | 0 |

## Conventions

- **Frontmatter**: Every SKILL.md has YAML frontmatter with `name`, `version`, `source`, `authority`, `data_as_of`, and `pipeline_position`
- **Reference YAML**: Every reference `.md` has YAML frontmatter with `title`, `category`, `relevance`, `key_topics`
- **Reference Routers**: Skills with 2+ references include a routing table mapping topics to specific reference files
- **Stop Conditions**: All skills define when to return partial artifacts instead of proceeding with unreliable data
- **External References**: Tabular format with Source, URL, and Use columns
