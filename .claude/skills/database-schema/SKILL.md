---
name: Database Schema
description: Use when defining, reviewing, or explaining what CoCivil's database should look like for parcel intelligence, redevelopment screening, site selection, and opportunity scoring.
---

## Use This Skill For

Use this skill when the task is about:

- what the database should look like
- why the database should be structured a certain way
- how to separate raw data, normalized data, and product-facing facts
- which tables should exist for parcel intelligence and opportunity finding
- how the database should evolve to support screening, ranking, and reporting

## Core Rule

The database should be explained as a three-layer system:

1. raw/source-of-truth
2. normalized domain tables
3. materialized parcel fact tables

## Read Next

Read the reference files:

- `references/database-schema.md` — target 3-layer architecture (what the DB should look like)
- `references/current-live-schema.md` — actual live schema captured from production Neon + Railway (what the DB looks like today)

Read these repo files only if needed for deeper grounding:

- `app/models/ingestion.py`
- `app/models/geospatial.py`
- `app/models/dataset.py`
- `app/models/policy.py`
- `app/models/facts.py`
- `docs/DATA_PLAN.md`
- `docs/TRACK_3_4_RESEARCH.md`

## Default Recommendation

If no other direction is given, recommend:

- strong provenance tables
- typed normalized parcel/zoning/policy/overlay tables
- materialized parcel fact tables for screening and ranking
- a search/ranking layer on top of parcel facts

Do not recommend a database that is only raw GIS layers or only AI/RAG outputs.
