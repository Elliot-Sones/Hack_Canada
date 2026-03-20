# Hack Canada — CoCivil Platform

## Auto-Update Rule for index.md

**After every file edit, creation, or deletion**, update `index.md` at the project root to reflect the change. The update should:
- Add new files with their path and a 1-line purpose description in the appropriate section
- Update the entry for modified files if their purpose or API surface changed
- Remove entries for deleted files
- Keep the "Last updated" date current
- Do NOT rewrite the whole file — only edit the relevant section(s)

This rule applies to all agents and Claude sessions working on this codebase.

Land-development due diligence platform for Toronto / Ontario.
Generates planning submission packages (planning rationale, compliance matrix, precedent report, etc.) from a plain-English development query.

---

## Project Structure

```
app/
  clients/        ArcGIS REST client
  data/           toronto_zoning.py, ontario_policy.py (runtime policy data)
  middleware/     request_id.py, idempotency.py
  models/         SQLAlchemy models (34 tables, PostGIS geometry)
  routers/        FastAPI route handlers (21 routers)
  schemas/        Pydantic request/response schemas
  services/       Business logic + submission/ document generation
  tasks/          Background task runners (plan pipeline, ingestion)
frontend/         Next.js 16 App Router + Better Auth
knowledge/        Domain knowledge for the app's AI (not coding docs)
                  research-pipeline/  — Ontario site-feasibility skills
                  document-templates/ — 29 planning document generators
                  water-policy/       — Ontario water/sewer policy docs
                  research/           — Data plans, implementation specs
fine-tuned-RAG/   ChromaDB ingestion pipeline (reads from knowledge/)
```

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + PostGIS
- **Frontend**: Next.js 16, App Router, Better Auth, MapLibre GL, Three.js, Konva.js
- **AI**: Claude (primary) or OpenAI (configurable via AI_PROVIDER), ChromaDB RAG
- **Spatial**: GeoAlchemy2, PostGIS, pyproj
- **Deploy**: Docker, Railway, AWS S3

## Coding Conventions

- **Async everywhere**: All DB access uses `async_session`. Services are async. Use `await` not `run_sync`.
- **Pydantic 2**: Schemas use `model_config = ConfigDict(...)`, not `class Config`.
- **Test naming**: `test_<module>_<behavior>.py`. Fixtures in `conftest.py`. Use `httpx.AsyncClient` via `ASGITransport`.
- **Imports**: Group as stdlib → third-party → local. Use absolute imports (`app.services.foo`).
- **Models**: Inherit from `Base`. Use `Mapped[T]` type annotations. GeoAlchemy2 for geometry columns.

---
