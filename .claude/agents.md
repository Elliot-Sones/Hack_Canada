# Agents — Arterial Platform

## index.md Auto-Update Protocol

Every agent working on this codebase must keep `index.md` current.

### When to update

Update `index.md` after:
- Creating a new file
- Deleting a file
- Modifying a file's public API surface (new functions, new routes, changed schemas)
- Adding or removing a Celery task
- Adding or removing an API endpoint
- Modifying a database model's key fields

### How to update

1. Read only the relevant section of `index.md` (do not rewrite the whole file)
2. Use `Edit` to make a targeted change
3. Update the "Last updated" date at the bottom

### Section map

| Change type | Section to edit |
|-------------|----------------|
| New/changed model | `## Backend — app/` → `### Database Models` |
| New/changed route | `## Backend — app/` → `### API Routes` + `## API Endpoint Reference` |
| New/changed service | `## Backend — app/` → `### Services` |
| New/changed Celery task | `## Backend — app/` → `### Background Tasks (Celery)` |
| New/changed schema | `## Backend — app/` → `### Schemas` |
| New/changed frontend component | `## Frontend — frontend-react/` → `### Components` |
| New/changed frontend utility | `## Frontend — frontend-react/` → `### Utilities` |
| New/changed config/infra file | `## Config & Infrastructure` |
| New/changed test file | `## Tests` |
| New/changed skill | `## .claude/ Skills Pipeline` |
| New known issue discovered | `## Known Issues & Incomplete Features` |

### Example edit (adding a new route)

After adding `GET /api/v1/parcels/{id}/massing-constraints` to `app/routers/parcels.py`:

1. Find the "Parcels" table in `### API Routes`
2. Add a new row: `| GET | /api/v1/parcels/{id}/massing-constraints | Massing constraints for parcel |`
3. Add a row to `## API Endpoint Reference`: `| GET | /api/v1/parcels/{id}/massing-constraints | Yes | No | ✓ |`
4. Update `*Last updated: YYYY-MM-DD*`

### Example edit (new service file)

After creating `app/services/citation_verifier.py`:

1. Find `### Services` table
2. Add: `| app/services/citation_verifier.py | Verifies AI-generated citations against policy source documents |`
3. Update last updated date.
