"""Run phases 3 (zoning) and 4 (constraints).

Phase 3 zoning features were already ingested. This script:
1. Assigns zone_codes to parcels via centroid-in-polygon
2. Populates zoning facts
3. Ingests constraint layers (heritage, ravine, ESA)
4. Populates constraint facts
"""
import sys
import time
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, ".")
from app.database import get_sync_db
from app.services.geospatial_ingestion import get_or_create_jurisdiction
from sqlalchemy import text
import structlog

logger = structlog.get_logger()

db = get_sync_db()
try:
    jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
    db.commit()
    jid = str(jurisdiction.id)

    # Phase 3: Zoning
    print("=" * 60)
    print("PHASE 3: Zoning")
    print("=" * 60)

    # Check if zoning features already exist
    r = db.execute(text("SELECT id FROM dataset_layers WHERE name = 'toronto_zoning_areas' LIMIT 1")).fetchone()
    if r:
        layer_id = str(r[0])
        print(f"\nZoning features already loaded (layer={layer_id[:8]}...)")

        print("\n[1/4] Assigning zone_codes to parcels via centroid...")
        t0 = time.monotonic()
        result = db.execute(text("""
            UPDATE parcels p
            SET zone_code = df.attributes_json->>'zone_code'
            FROM dataset_features df
            WHERE df.dataset_layer_id = CAST(:layer_id AS uuid)
                AND ST_Contains(df.geom, ST_Centroid(p.geom))
                AND p.jurisdiction_id = CAST(:jid AS uuid)
        """), {"layer_id": layer_id, "jid": jid})
        db.commit()
        print(f"  Updated {result.rowcount:,} parcels ({time.monotonic() - t0:.0f}s)")
    else:
        print("\nNo zoning features found — running full ingestion...")
        from app.services.arcgis_ingestion import ingest_arcgis_zoning
        t0 = time.monotonic()
        summary = ingest_arcgis_zoning(db, jurisdiction.id)
        print(f"  Zoning: {summary.processed:,} inserted ({time.monotonic() - t0:.0f}s)")

    print("\n[2/4] Populating parcel_zoning_facts...")
    from app.services.fact_population import populate_parcel_zoning_facts
    t0 = time.monotonic()
    fact_count = populate_parcel_zoning_facts(db, jurisdiction.id)
    print(f"  Zoning facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

    # Phase 4: Constraints
    print("\n" + "=" * 60)
    print("PHASE 4: Constraints")
    print("=" * 60)

    print("\n[3/4] Ingesting constraints (heritage, ravine, ESA)...")
    from app.services.arcgis_ingestion import ingest_arcgis_constraints
    t0 = time.monotonic()
    results = ingest_arcgis_constraints(db, jurisdiction.id)
    elapsed = time.monotonic() - t0
    for name, s in results.items():
        print(f"  {name}: {s.processed:,} inserted, {s.failed:,} failed")
    print(f"  ({elapsed:.0f}s total)")

    print("\n[4/4] Populating parcel_constraint_facts...")
    from app.services.fact_population import populate_parcel_constraint_facts
    t0 = time.monotonic()
    fact_count = populate_parcel_constraint_facts(db, jurisdiction.id)
    print(f"  Constraint facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

    print("\nPhases 3-4 complete!")
except Exception as e:
    print(f"\nFAILED: {e}", file=sys.stderr)
    raise
finally:
    db.close()
