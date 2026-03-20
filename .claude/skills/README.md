# Coding Skills — `.claude/skills/`

This directory contains **coding skills** that help Claude Code write correct code for this codebase. These are NOT domain knowledge or research pipeline docs — those live in `knowledge/`.

## What Belongs Here

Skills that teach the coding agent about:
- Database schema, model patterns, migration conventions
- API patterns, router structure, service layer conventions
- Testing patterns and fixture setup

## Current Skills

| Skill | Purpose |
|-------|---------|
| `database-schema/` | Full DB architecture, table relationships, live schema reference |

## What Does NOT Belong Here

- Ontario planning policy, zoning by-laws, building code → `knowledge/research-pipeline/`
- Document generation templates → `knowledge/document-templates/`
- Water/sewer policy docs → `knowledge/water-policy/`
- Research plans and specs → `knowledge/research/`
