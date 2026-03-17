# Database Schema

## What The Database Needs To Do

The database should help the product answer:

- what parcel is this
- what is built on it
- what rules apply to it
- what hard constraints affect it
- whether it is a good opportunity
- how it compares to other parcels

That means the database is not just for storage. It is also for decision-making.

## The Database Should Have 3 Layers

### 1. Raw / Source-of-Truth Layer

This layer stores the original imported data and its history.

Examples:

- source snapshots
- ingestion jobs
- parse artifacts
- review queue
- refresh schedules

Why this layer exists:

- outside data changes over time
- parsers improve over time
- reports need to be reproducible
- low-confidence extraction needs human review

This layer preserves truth.

### 2. Normalized Domain Layer

This layer stores clean, structured business entities.

Main domains:

- parcels
- addresses
- zoning assignments
- GIS overlays
- policy documents and clauses
- permits / applications / precedents
- financial and simulation defaults

Why this layer exists:

- outside sources are messy
- different cities use different names and formats
- the app needs stable internal structures
- zoning, overlays, and policy are different concepts and should stay separate

This layer preserves meaning.

### 3. Materialized Parcel Fact Layer

This layer stores ready-to-use parcel answers.

Examples:

- the parcel is in a floodplain
- the parcel is underutilized
- the parcel allows mixed use
- the parcel has one building
- the redevelopment score is high

Why this layer exists:

- the product needs fast search, filtering, ranking, and explanation
- common parcel answers should not be recomputed from scratch on every request
- opportunity identification needs precomputed parcel-level facts

This layer powers the product.

## Why This Is The Right Shape

Without the first layer:

- you lose provenance
- you cannot easily re-run processing
- you cannot explain what source version was used

Without the second layer:

- everything stays messy
- every feature has to understand source-specific field names
- domain logic becomes tangled

Without the third layer:

- the system can describe parcels, but not screen or rank them well
- APIs stay slower
- district-wide opportunity workflows become awkward

So the correct pattern is:

```text
original data
-> cleaned structured data
-> parcel facts
-> product features
```

## What Tables Should Exist

### Raw / Source-of-Truth Tables

Keep or support tables like:

- `source_snapshots`
- `ingestion_jobs`
- `snapshot_manifests`
- `parse_artifacts`
- `review_queue_items`
- `refresh_schedules`

Purpose:

- track where data came from
- track when it changed
- track how it was processed

### Normalized Parcel Tables

Core parcel tables should include:

- `jurisdictions`
- `parcels`
- `parcel_addresses`
- `parcel_metrics`
- `parcel_zoning_assignments`
- `project_parcels`

Purpose:

- parcels are the anchor entity
- addresses need their own linkage and confidence logic
- zoning assignment should be explicit

### Normalized GIS Tables

Core GIS tables should include:

- `dataset_layers`
- `dataset_features`
- `feature_to_parcel_links`

Purpose:

- hold generic map layers such as overlays
- support parcel-to-feature relationships

Important rule:

These tables are good for GIS layers, but should not become a dumping ground for every data type.

### Normalized Policy Tables

Core policy tables should include:

- `policy_documents`
- `policy_versions`
- `policy_clauses`
- `policy_references`
- `policy_applicability_rules`
- `policy_review_items`

Purpose:

- store planning rules as a structured citation graph
- keep legal text, normalized rules, and applicability separate but linked

## What Fact Tables Should Exist

### `parcel_current_facts`

Purpose:

- basic current parcel profile

Typical fields:

- parcel id
- jurisdiction id
- current snapshot id
- canonical address
- pin
- lot area
- frontage
- depth
- current use
- primary zone code

### `parcel_building_facts`

Purpose:

- summarize existing built form

Typical fields:

- building count
- total footprint area
- building coverage percent
- vacant lot flag
- underutilized flag

### `parcel_constraint_facts`

Purpose:

- summarize hard constraints

Typical fields:

- heritage flag
- floodplain flag
- ravine/environment flag
- coverage percentages
- summary json

### `parcel_zoning_facts`

Purpose:

- store actionable zoning answers

Typical fields:

- zone code
- zone family
- max height
- max storeys
- max FSI
- setbacks
- lot coverage
- permitted uses
- warnings

### `parcel_policy_facts`

Purpose:

- connect parcels to applicable policy records

Typical fields:

- policy manifest id
- applicable clause ids
- secondary plan ids
- SASP ids
- summary json

### `parcel_precedent_facts`

Purpose:

- summarize nearby planning history

Typical fields:

- nearby application count
- approved count
- refused count
- rezoning count
- summary json

### `parcel_opportunity_facts`

Purpose:

- support screening and ranking

Typical fields:

- redevelopment score
- target-use-fit score
- reason codes
- district eligibility flags
- underbuilt-relative-to-zoning flag
- recommended use tags

### `parcel_search_index`

Purpose:

- support fast parcel search and filtering

Typical fields:

- address text
- zoning tags
- district tags
- use flags
- constraint flags
- size metrics
- score columns

## What The API Should Prefer

The product should prefer:

1. fact tables first
2. normalized tables second
3. RAG or narrative generation third

That means:

- facts answer what is true and useful
- normalized tables backstop the facts
- AI explains, summarizes, or fills gaps

## What To Avoid

Avoid:

- recomputing common GIS intersections on every request
- using RAG as the main source of parcel truth
- mixing raw source records with product recommendations
- storing every concept in generic GIS tables
- designing only for one-parcel deep dive when the product needs multi-parcel screening

## Why This Matters For The Product

This database shape supports:

- parcel search
- district-wide screening
- redevelopment ranking
- explainable parcel detail
- reproducible reports
- easier multi-city expansion

Without the fact layer, the app stays mostly a parcel reader.
With the fact layer, it becomes an opportunity identification platform.

## What Is Non-Negotiable

These parts are the strongest requirements:

- provenance/source tracking
- typed normalized parcel/zoning/policy tables
- materialized parcel fact tables

These exact fact tables can change, but the three-layer pattern should stay.
