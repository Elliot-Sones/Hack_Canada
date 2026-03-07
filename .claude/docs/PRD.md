# PRD: Policy-Aware Buildability Intelligence Pipeline

## 1. Overview

### Product name

Buildability Intelligence Pipeline

### Product vision

Create a policy-aware research and analysis pipeline that answers a high-value development question:

**“Can we build this on this site, under current public rules and constraints?”**

The system will ingest publicly accessible parcel, zoning, policy, and contextual data; normalize it; run structured analysis through modular subagents; and produce a defensible, source-backed buildability report.

The product is not meant to replace a planner, architect, lawyer, or engineer. Its purpose is to accelerate early-stage feasibility screening and reduce manual review time for development teams, land acquisition teams, consultants, and urban tech operators.

### Problem statement

Today, early-stage site feasibility work is slow, fragmented, and manual. Users often need to search across municipal zoning by-laws, official plans, parcel records, maps, overlays, council materials, and related planning documents before they can form even a preliminary view on whether a project is viable. This creates several problems:

* Relevant information is spread across many public sources
* Policies are difficult to interpret consistently
* Manual research is time-consuming and expensive
* Early assessments are often not standardized or auditable
* Teams struggle to separate hard rules, soft guidance, and unknowns

### Proposed solution

Build a pipeline that:

1. Accepts a location, parcel, or project concept
2. Finds and gathers relevant public data sources
3. Extracts and normalizes policy-relevant information
4. Runs modular analysis through specialized subagents
5. Produces a report that clearly distinguishes facts, inferences, assumptions, and unknowns
6. Surfaces risks, missing information, and confidence levels

---

## 2. Goals and Non-Goals

### Goals

* Help users evaluate site feasibility using publicly accessible information
* Reduce time required for initial policy and parcel research
* Provide structured, traceable, source-backed outputs
* Support a modular multi-agent pipeline with reusable skills
* Build an MVP that can support one geography or jurisdiction well before expanding
* Keep human review easy by preserving provenance and confidence scores

### Non-goals

* Issuing legal advice
* Replacing formal planning, legal, or architectural review
* Guaranteeing permit or entitlement outcomes
* Scraping high-risk or access-restricted data where safer alternatives exist
* Supporting all jurisdictions from day one
* Producing final engineering or stamped compliance outputs

---

## 3. Target Users

### Primary users

* Real estate developers
* Land acquisition teams
* Urban planners
* Architecture and planning consultants
* Proptech operators
* Research analysts screening sites at scale

### Secondary users

* Municipal policy researchers
* Investment teams evaluating land opportunities
* Student or startup teams building feasibility tooling

### User jobs to be done

* “Tell me whether this parcel can support the project type I want.”
* “Show me the rules that matter for this site.”
* “Summarize the major constraints, opportunities, and unknowns.”
* “Find parcels that match my target build profile.”
* “Generate a preliminary feasibility memo with citations.”

---

## 4. Core User Stories

### MVP user stories

1. As a user, I can input an address, parcel identifier, or map location to start a project.
2. As a user, I can specify a proposed project concept such as residential, mixed-use, or low-rise multifamily.
3. As a user, I receive a structured report showing applicable public rules, likely constraints, and major unknowns.
4. As a user, I can inspect the sources used for each conclusion.
5. As a user, I can see what was confirmed, inferred, or not verifiable.
6. As a user, I can export the analysis into a readable report.

### V2 user stories

1. As a user, I can compare multiple parcels at once.
2. As a user, I can search for parcels that fit a development profile.
3. As a user, I can upload my own assumptions or project inputs.
4. As a user, I can rerun analysis when policies or datasets are updated.
5. As a user, I can collaborate with teammates and track revisions.

---

## 5. Product Scope

### MVP scope

The MVP will support a focused workflow:

* One target jurisdiction or metro area
* One primary site feasibility question: “Can a project of type X likely be pursued here?”
* Publicly accessible data only
* Strong source traceability
* Human-readable report generation
* Modular subagent orchestration

### Out of scope for MVP

* National coverage
* Permit submission automation
* Automated legal interpretation beyond structured policy extraction
* Closed vendor datasets unless licensed
* Full GIS authoring suite
* Financial underwriting engine
* Engineering design automation

---

## 6. Product Requirements

### Functional requirements

#### Input and project creation

* Users must be able to create a project from address, parcel ID, or map-based selection
* Users must be able to specify intended use type and optional high-level assumptions
* The system must store project state, source bundle, intermediate artifacts, and final outputs

#### Source discovery

* The system must identify relevant public sources for a parcel or area
* The system must classify source type, trust level, access method, freshness, and restrictions
* The system must store source provenance for downstream review

#### Data extraction and normalization

* The system must extract policy-relevant content from supported sources
* The system must normalize extracted content into a structured schema
* The system must preserve citations to source URLs and sections where possible
* The system must flag extraction uncertainty and unresolved fields

#### Analysis

* The system must distinguish between:

  * verified facts
  * structured inferences
  * assumptions
  * unknowns
* The system must identify key feasibility constraints such as permitted use, density, height, setbacks, overlays, and special controls where data is available
* The system must generate a clear summary of opportunities, blockers, and items requiring human review

#### Output generation

* The system must generate a structured report with citations and confidence levels
* The system must support export to JSON and human-readable markdown or PDF-ready output
* The system must expose intermediate artifacts for auditability

#### Pipeline orchestration

* The system must support asynchronous long-running jobs
* The system must show job state and progress updates
* The system must support retries, failure handling, and partial completion
* The system must support modular subagents with explicit input/output contracts

### Non-functional requirements

* Source traceability is required for all material claims
* The system should be auditable and easy to review by a human analyst
* New geographies should be addable via modular source adapters and skills
* The system should avoid hidden black-box conclusions
* The system should degrade gracefully when data is missing
* The system should support isolated worker execution for long-running or tool-using tasks

---

## 7. Proposed System Architecture

### Architectural principle

The system should be designed around **artifacts and contracts**, not around vague agent behavior.

Each stage must produce a concrete artifact that the next stage consumes.

### High-level architecture

Frontend / UI
→ API layer
→ Persistent orchestrator / job manager
→ Queue and state store
→ Subagents / workers
→ Database, object storage, and realtime updates

### Subagents

#### 1. Source Discovery Agent

Purpose:
Find relevant public data sources for the project site and project type.

Inputs:

* Project location or parcel
* Jurisdiction
* Project type

Outputs:

* `source_bundle.json`

Responsibilities:

* Identify source URLs
* Classify sources by type and trust level
* Record access method and restrictions
* Score relevance and freshness

#### 2. Extraction and Normalization Agent

Purpose:
Convert source documents into canonical structured records.

Inputs:

* `source_bundle.json`

Outputs:

* `normalized_data.json`

Responsibilities:

* Parse policy text, tables, maps, metadata, and parcel attributes where supported
* Normalize fields into consistent schema
* Preserve citations and unresolved ambiguities

#### 3. Analysis Agent

Purpose:
Evaluate the parcel or site against extracted policy-relevant data.

Inputs:

* `normalized_data.json`
* User project assumptions

Outputs:

* `analysis_packet.json`

Responsibilities:

* Determine applicable rules where possible
* Summarize likely feasibility constraints and opportunities
* Separate facts, inferences, assumptions, and unknowns
* Assign confidence levels

#### 4. QA and Compliance Agent

Purpose:
Audit outputs for unsupported claims, provenance gaps, and risk flags.

Inputs:

* `source_bundle.json`
* `normalized_data.json`
* `analysis_packet.json`

Outputs:

* `review_packet.json`

Responsibilities:

* Check source support for claims
* Flag weak or missing citations
* Flag potential policy, scraping, or licensing concerns
* Detect contradictions across artifacts

#### 5. Report Generator Agent

Purpose:
Produce the final user-facing report.

Inputs:

* All upstream artifacts

Outputs:

* `final_report.json`
* human-readable report

Responsibilities:

* Assemble readable narrative and structured summary
* Display confidence, gaps, and next steps
* Format output for export

---

## 8. Team Responsibilities

### Person 1: Skills and Analysis

Owns:

* Skill design
* Analysis prompts and tool definitions
* Extraction logic templates
* Evaluation cases
* Confidence and reasoning framework

Deliverables:

* Skill specifications
* Input/output schemas for agent stages
* Evaluation dataset and expected outputs
* Prompt and rules library

### Person 2: Data and Source Research

Owns:

* Public source discovery
* Source registry
* Schema mapping
* Provenance standards
* Source restrictions log

Deliverables:

* Source inventory
* Source taxonomy
* Data dictionary
* Freshness and update rules
* Risk classification by source

### Person 3: Pipeline and Orchestration

Owns:

* API and project lifecycle
* Job orchestration and queueing
* Agent execution order
* Persistence and storage
* Observability and failure handling
* Final artifact assembly

Deliverables:

* Job state machine
* Orchestration service
* Artifact storage model
* Realtime status layer
* Retry and timeout policy

---

## 9. Data Model and Artifacts

### Core artifacts

#### `source_bundle.json`

Contains:

* source ID
* URL
* title
* source type
* trust level
* access method
* freshness
* restrictions
* relevance score

#### `normalized_data.json`

Contains:

* parcel metadata
* zoning fields
* policy controls
* overlays
* document excerpts
* citations
* unresolved fields
* extraction confidence

#### `analysis_packet.json`

Contains:

* project summary
* feasibility findings
* applicable controls
* blockers
* opportunities
* assumptions
* unknowns
* confidence levels

#### `review_packet.json`

Contains:

* unsupported claim flags
* provenance gaps
* compliance notes
* contradictions
* recommended human review items

#### `final_report.json`

Contains:

* executive summary
* detailed findings
* policy summary
* risk summary
* source appendix
* confidence scoring

### Core entities

* Project
* Parcel or site
* Jurisdiction
* Source
* Extracted rule
* Constraint
* Opportunity
* Assumption
* Unknown
* Report

---

## 10. Data Requirements

### Essential MVP data

* Parcel or site identifier
* Jurisdiction boundary context
* Zoning designation
* Permitted use information
* Basic development controls where publicly available

  * height
  * density or FSI/FAR
  * setbacks
  * lot coverage
  * minimum lot size
* Official planning or land-use policy references
* Source URLs and provenance metadata

### Useful but optional data

* Heritage overlays
* Environmental constraints
* Urban design guidelines
* Transit proximity
* Existing building data
* Development application precedents
* Planning staff reports
* Public hearing or council materials
* Market or demographic context
* Map layers and geospatial enrichments

### Hard-to-obtain or high-risk data

* Proprietary parcel ownership datasets
* Licensed assessor data
* Access-restricted permit systems
* Closed GIS layers without open licensing
* Private brokerage datasets
* User-hostile or terms-restricted web content
* Sensitive personal information

---

## 11. Source Strategy

### Preferred source hierarchy

1. Official municipal or regional APIs
2. Official GIS portals and open data catalogs
3. Official planning documents and zoning by-laws
4. Official parcel viewers and map services
5. User-provided documents
6. Licensed datasets and partnerships
7. Public web pages with clear permission or permissive terms

### Last-resort sources

* Unofficial mirrors
* Fragile HTML pages without stable structure
* Sites with restrictive anti-scraping terms
* Content behind login, paywalls, or access controls

---

## 12. Compliance and Risk Principles

### Compliance principles

* Use public information only unless properly licensed or user-provided
* Preserve source provenance for every material conclusion
* Avoid collecting unnecessary personal data
* Do not bypass access controls
* Prefer official APIs and open datasets over scraping
* Flag licensing and terms uncertainty explicitly

### Risk categories

#### Legal and contractual risk

* Violating website terms of service
* Breaching data licensing restrictions
* Reusing content in ways not permitted

#### Technical risk

* Fragile scrapers breaking due to source changes
* Inconsistent schemas across jurisdictions
* Poor-quality OCR or extraction errors

#### Product risk

* False confidence from incomplete data
* Users over-relying on preliminary outputs
* Difficulty scaling across municipalities with different rules

#### Compliance risk

* Incorrectly representing inferred conclusions as confirmed facts
* Failing to disclose unknowns or missing source coverage

---

## 13. UX and Output Requirements

### Report structure

The final report should include:

* Executive summary
* Site and project input summary
* Applicable policy and rules snapshot
* Key constraints and opportunities
* Facts vs inferences vs assumptions vs unknowns
* Risk and confidence summary
* Source appendix
* Recommended next human-review steps

### UX principles

* Make source-backed reasoning inspectable
* Surface uncertainty clearly
* Keep the report understandable for non-experts
* Allow users to drill into citations and raw artifacts
* Show job progress during long-running analyses

---

## 14. Success Metrics

### MVP metrics

* Time to first usable feasibility report
* Percentage of claims with supporting source citations
* Analyst review satisfaction
* Reduction in manual research time
* Successful completion rate of pipeline jobs
* Percentage of outputs with explicit unknowns and confidence fields

### Quality metrics

* Source precision rate
* Extraction accuracy on test set
* Unsupported-claim rate
* False-confidence rate
* Human override or correction frequency

---

## 15. Rollout Plan

### Phase 0: Design and contracts

* Finalize PRD
* Define source taxonomy
* Define artifact schemas
* Define supported jurisdiction and project types

### Phase 1: MVP pipeline

* Project creation flow
* Source discovery
* Basic extraction and normalization
* Analysis agent
* Report generation
* Manual QA support

### Phase 2: Reliability and auditability

* Add job retries and observability
* Add compliance agent
* Add export and version history
* Improve confidence scoring

### Phase 3: Expansion

* Add more jurisdictions
* Add parcel search by build criteria
* Add user-uploaded document support
* Add richer map and precedent layers

---

## 16. Open Questions

* Which jurisdiction should the MVP support first?
* What exact source types are considered in-scope for MVP?
* Will the MVP use geospatial APIs directly or rely on simpler parcel/address inputs first?
* What output format matters most initially: web report, JSON, or PDF export?
* How much structured analysis can be automated before human review is mandatory?
* Which data sources require explicit legal review before use?

---

## 17. Recommended Technical Approach

### MVP recommendation

Build a queue-backed orchestrated system with three logical stages first:

* Research stage
* Analysis stage
* Report stage

Internally, these can still map to subagents, but the external pipeline remains simple and reliable.

### Why this approach

* Easier for a 3-person team to ship
* Preserves the CrossBeam-style modularity without overcomplicating the MVP
* Supports long-running jobs and future isolation of agent workers
* Makes artifacts and review flows explicit from the start

### Suggested MVP stack

* Frontend: Next.js or equivalent
* API and orchestrator: Node.js/TypeScript
* Queue: Redis/BullMQ or equivalent
* Database: Postgres
* Object storage: S3-compatible storage
* Realtime updates: websocket or database-backed realtime layer
* Worker execution: containerized or isolated worker processes

---

## 18. Final Product Principle

This product must optimize for **trustworthy early-stage feasibility intelligence**, not flashy black-box outputs.

Every meaningful conclusion should be traceable, confidence-scored, and easy to challenge.

The core differentiator is not just data collection. It is the ability to transform fragmented public policy and site data into a structured, auditable, and decision-useful workflow.
