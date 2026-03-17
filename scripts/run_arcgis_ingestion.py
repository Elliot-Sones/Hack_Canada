"""Run ArcGIS ingestion directly against the database (no Celery needed)."""

from __future__ import annotations

import sys
import time

from dotenv import load_dotenv
load_dotenv()

from app.database import get_sync_db
from app.services.geospatial_ingestion import get_or_create_jurisdiction


def run_phase1():
    """Phase 1: Parcels + Addresses + Current Facts."""
    from app.services.arcgis_ingestion import ingest_arcgis_parcels, ingest_arcgis_addresses
    from app.services.fact_population import populate_parcel_current_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        print("=" * 60)
        print("PHASE 1: Parcels + Addresses")
        print("=" * 60)

        print("\n[1/3] Ingesting parcels from ArcGIS...")
        t0 = time.monotonic()
        parcel_summary = ingest_arcgis_parcels(db, jurisdiction.id)
        print(f"  Parcels: {parcel_summary.processed:,} inserted, {parcel_summary.failed:,} failed ({time.monotonic() - t0:.0f}s)")

        print("\n[2/3] Ingesting address points from ArcGIS...")
        t0 = time.monotonic()
        addr_summary = ingest_arcgis_addresses(db, jurisdiction.id)
        print(f"  Addresses: {addr_summary.processed:,} matched, {addr_summary.failed:,} failed ({time.monotonic() - t0:.0f}s)")

        print("\n[3/3] Populating parcel_current_facts...")
        t0 = time.monotonic()
        fact_count = populate_parcel_current_facts(db, jurisdiction.id)
        print(f"  Current facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

        print("\nPhase 1 complete!")
    except Exception as e:
        print(f"\nPhase 1 FAILED: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


def run_phase2():
    """Phase 2: Buildings + Building Facts."""
    from app.services.arcgis_ingestion import ingest_arcgis_buildings, link_buildings_to_parcels
    from app.services.fact_population import populate_parcel_building_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        print("=" * 60)
        print("PHASE 2: Building Footprints")
        print("=" * 60)

        print("\n[1/3] Ingesting building footprints from ArcGIS...")
        t0 = time.monotonic()
        summary = ingest_arcgis_buildings(db, jurisdiction.id)
        print(f"  Buildings: {summary.processed:,} inserted, {summary.failed:,} failed ({time.monotonic() - t0:.0f}s)")

        print("\n[2/3] Linking buildings to parcels...")
        t0 = time.monotonic()
        links = link_buildings_to_parcels(db, jurisdiction.id)
        print(f"  Links: {links:,} created ({time.monotonic() - t0:.0f}s)")

        print("\n[3/3] Populating parcel_building_facts...")
        t0 = time.monotonic()
        fact_count = populate_parcel_building_facts(db, jurisdiction.id)
        print(f"  Building facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

        print("\nPhase 2 complete!")
    except Exception as e:
        print(f"\nPhase 2 FAILED: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


def run_phase3():
    """Phase 3: Zoning + Zoning Facts."""
    from app.services.arcgis_ingestion import ingest_arcgis_zoning
    from app.services.fact_population import populate_parcel_zoning_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        print("=" * 60)
        print("PHASE 3: Zoning")
        print("=" * 60)

        print("\n[1/2] Ingesting zoning areas from ArcGIS...")
        t0 = time.monotonic()
        summary = ingest_arcgis_zoning(db, jurisdiction.id)
        print(f"  Zoning features: {summary.processed:,} inserted, {summary.failed:,} failed ({time.monotonic() - t0:.0f}s)")

        print("\n[2/2] Populating parcel_zoning_facts...")
        t0 = time.monotonic()
        fact_count = populate_parcel_zoning_facts(db, jurisdiction.id)
        print(f"  Zoning facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

        print("\nPhase 3 complete!")
    except Exception as e:
        print(f"\nPhase 3 FAILED: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


def run_phase4():
    """Phase 4: Constraints + Constraint Facts."""
    from app.services.arcgis_ingestion import ingest_arcgis_constraints
    from app.services.fact_population import populate_parcel_constraint_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        print("=" * 60)
        print("PHASE 4: Constraint Overlays")
        print("=" * 60)

        print("\n[1/2] Ingesting heritage, ravine, ESA from ArcGIS...")
        t0 = time.monotonic()
        results = ingest_arcgis_constraints(db, jurisdiction.id)
        elapsed = time.monotonic() - t0
        for name, summary in results.items():
            print(f"  {name}: {summary.processed:,} inserted, {summary.failed:,} failed")
        print(f"  ({elapsed:.0f}s total)")

        print("\n[2/2] Populating parcel_constraint_facts...")
        t0 = time.monotonic()
        fact_count = populate_parcel_constraint_facts(db, jurisdiction.id)
        print(f"  Constraint facts: {fact_count:,} upserted ({time.monotonic() - t0:.0f}s)")

        print("\nPhase 4 complete!")
    except Exception as e:
        print(f"\nPhase 4 FAILED: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    phases = sys.argv[1:] if len(sys.argv) > 1 else ["1", "2", "3", "4"]
    total_start = time.monotonic()

    for phase in phases:
        if phase == "1":
            run_phase1()
        elif phase == "2":
            run_phase2()
        elif phase == "3":
            run_phase3()
        elif phase == "4":
            run_phase4()
        else:
            print(f"Unknown phase: {phase}")
            print("Usage: python scripts/run_arcgis_ingestion.py [1] [2] [3] [4]")
            sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"ALL DONE in {time.monotonic() - total_start:.0f}s")
    print(f"{'=' * 60}")
