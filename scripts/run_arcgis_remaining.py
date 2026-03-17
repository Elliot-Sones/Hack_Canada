"""Run remaining: building facts + phases 3 & 4."""
import sys
import time
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, ".")
from app.database import get_sync_db
from app.services.geospatial_ingestion import get_or_create_jurisdiction
from app.services.fact_population import populate_parcel_building_facts
from app.services.arcgis_ingestion import (
    ingest_arcgis_zoning,
    ingest_arcgis_constraints,
)
from app.services.fact_population import (
    populate_parcel_zoning_facts,
    populate_parcel_constraint_facts,
)

db = get_sync_db()
try:
    jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
    db.commit()

    # Building facts (buildings + links already done)
    print("=" * 60)
    print("[1/5] Populating parcel_building_facts...")
    t0 = time.monotonic()
    fact_count = populate_parcel_building_facts(db, jurisdiction.id)
    print(f"  Building facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

    # Phase 3: Zoning
    print("\n" + "=" * 60)
    print("[2/5] Ingesting zoning areas from ArcGIS...")
    t0 = time.monotonic()
    summary = ingest_arcgis_zoning(db, jurisdiction.id)
    print(f"  Zoning: {summary.processed:,} inserted, {summary.failed:,} failed ({time.monotonic() - t0:.0f}s)")

    print("\n[3/5] Populating parcel_zoning_facts...")
    t0 = time.monotonic()
    fact_count = populate_parcel_zoning_facts(db, jurisdiction.id)
    print(f"  Zoning facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

    # Phase 4: Constraints
    print("\n" + "=" * 60)
    print("[4/5] Ingesting constraints (heritage, ravine, ESA)...")
    t0 = time.monotonic()
    results = ingest_arcgis_constraints(db, jurisdiction.id)
    elapsed = time.monotonic() - t0
    for name, s in results.items():
        print(f"  {name}: {s.processed:,} inserted, {s.failed:,} failed")
    print(f"  ({elapsed:.0f}s total)")

    print("\n[5/5] Populating parcel_constraint_facts...")
    t0 = time.monotonic()
    fact_count = populate_parcel_constraint_facts(db, jurisdiction.id)
    print(f"  Constraint facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

    print("\nAll remaining phases complete!")
except Exception as e:
    print(f"\nFAILED: {e}", file=sys.stderr)
    raise
finally:
    db.close()
