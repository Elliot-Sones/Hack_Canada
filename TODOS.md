# TODOS

## Mobile Multi-Select Support
**What:** Add touch-friendly multi-select for map parcels (long-press or "Compare mode" toggle button)
**Why:** Ctrl+Click multi-select doesn't work on touchscreens — the comparison feature is desktop-only
**Pros:** Completes the multi-select feature for all device types
**Cons:** ~1-2 hours of touch event handling + UI toggle button design
**Context:** SelectionChips.jsx already renders on mobile, users just can't add parcels to it via touch. A "Compare mode" toggle in the map controls that switches tap behavior from "select single" to "add to comparison" is the cleanest pattern. See how Google Maps handles multi-stop directions for inspiration.
**Depends on:** Map-click parcel selection PR shipping first
**Added:** 2026-03-17

## Vector Tile Server for Parcels
**What:** Replace bbox GeoJSON loading with vector tiles via pg_tileserv or Martin
**Why:** Current approach loads up to 500 parcels as GeoJSON on every map pan — won't scale beyond Toronto
**Pros:** Instant parcel rendering at any zoom, no 500-parcel cap, sub-50ms responses, province-wide support
**Cons:** New infrastructure dependency (tile server), deployment complexity, 2-4 hours setup
**Context:** PostGIS + existing `parcels` table is tile-server-ready. Martin (Rust-based) or pg_tileserv (Go-based) can serve MVT tiles directly from the table. The frontend MapView would switch `parcels-bbox` from a GeoJSON source to a vector tile source. Click/hover/feature-state patterns stay the same. Railway deployment would need a second service.
**Depends on:** Map-click parcel selection PR establishing the interaction pattern
**Added:** 2026-03-17

## Cache Invalidation After Ingestion
**What:** Clear cached parcel data when CKAN/ArcGIS ingestion updates parcel/zoning/overlay records
**Why:** Cached responses serve stale data for up to 24h after ingestion. Bulk invalidation ensures users see fresh data immediately.
**Pros:** Guarantees data freshness after ingestion runs
**Cons:** Adds coupling between ingestion tasks and cache keys. Ingestion is infrequent (weekly/monthly) so impact is low.
**Context:** `app/tasks/ingestion.py` should call `redis.delete(f"cocivil:parcel:{id}")` etc. after each parcel upsert, or do a bulk `SCAN cocivil:* | DEL` after ingestion completes. The 24h TTL self-corrects regardless, but explicit invalidation is cleaner. Cache key patterns to invalidate: `cocivil:parcel:*` (24h TTL), `cocivil:zoning:*` (24h), `cocivil:overlays:*` (24h), `cocivil:policy:*` (1h), `cocivil:search:*` (5min), `cocivil:snapshots:*` (60s).
**Depends on:** Redis caching layer (app/services/cache.py)
**Added:** 2026-03-18
