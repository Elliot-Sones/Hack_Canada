"""Run just addresses + current facts (parcels already done)."""
import sys
import time
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, ".")
from app.database import get_sync_db
from app.services.geospatial_ingestion import get_or_create_jurisdiction
from app.services.arcgis_ingestion import ingest_arcgis_addresses
from app.services.fact_population import populate_parcel_current_facts

db = get_sync_db()
try:
    jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
    db.commit()

    print("[1/2] Ingesting address points from ArcGIS...")
    t0 = time.monotonic()
    addr_summary = ingest_arcgis_addresses(db, jurisdiction.id)
    print(f"  Addresses: {addr_summary.processed:,} matched, {addr_summary.failed:,} failed ({time.monotonic() - t0:.0f}s)")

    print("[2/2] Populating parcel_current_facts...")
    t0 = time.monotonic()
    fact_count = populate_parcel_current_facts(db, jurisdiction.id)
    print(f"  Current facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

    print("Done!")
finally:
    db.close()
