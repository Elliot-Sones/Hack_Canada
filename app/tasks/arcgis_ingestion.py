"""Background Celery tasks for ArcGIS data ingestion and fact table population."""

import structlog

from app.celery_app import celery
from app.database import get_sync_db
from app.services.geospatial_ingestion import get_or_create_jurisdiction

logger = structlog.get_logger()


@celery.task(bind=True, max_retries=2)
def ingest_arcgis_parcels_task(self):
    """Phase 1a: Ingest Toronto property boundaries from ArcGIS."""
    from app.services.arcgis_ingestion import ingest_arcgis_parcels
    from app.services.fact_population import populate_parcel_current_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        parcel_summary = ingest_arcgis_parcels(db, jurisdiction.id)
        logger.info("arcgis_task.parcels.done", processed=parcel_summary.processed)

        # Also ingest addresses and populate current facts
        from app.services.arcgis_ingestion import ingest_arcgis_addresses
        addr_summary = ingest_arcgis_addresses(db, jurisdiction.id)
        logger.info("arcgis_task.addresses.done", processed=addr_summary.processed)

        fact_count = populate_parcel_current_facts(db, jurisdiction.id)
        logger.info("arcgis_task.current_facts.done", upserted=fact_count)

        return {
            "status": "completed",
            "parcels_processed": parcel_summary.processed,
            "parcels_failed": parcel_summary.failed,
            "addresses_processed": addr_summary.processed,
            "current_facts_upserted": fact_count,
        }
    except Exception as e:
        logger.error("arcgis_task.parcels.failed", error=str(e))
        raise
    finally:
        db.close()


@celery.task(bind=True, max_retries=2)
def ingest_arcgis_buildings_task(self):
    """Phase 2: Ingest Toronto building footprints from ArcGIS."""
    from app.services.arcgis_ingestion import ingest_arcgis_buildings, link_buildings_to_parcels
    from app.services.fact_population import populate_parcel_building_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        summary = ingest_arcgis_buildings(db, jurisdiction.id)
        logger.info("arcgis_task.buildings.done", processed=summary.processed)

        links = link_buildings_to_parcels(db, jurisdiction.id)
        logger.info("arcgis_task.buildings.linked", links=links)

        fact_count = populate_parcel_building_facts(db, jurisdiction.id)
        logger.info("arcgis_task.building_facts.done", upserted=fact_count)

        return {
            "status": "completed",
            "buildings_processed": summary.processed,
            "buildings_failed": summary.failed,
            "parcel_links": links,
            "building_facts_upserted": fact_count,
        }
    except Exception as e:
        logger.error("arcgis_task.buildings.failed", error=str(e))
        raise
    finally:
        db.close()


@celery.task(bind=True, max_retries=2)
def ingest_arcgis_zoning_task(self):
    """Phase 3: Ingest Toronto zoning areas from ArcGIS."""
    from app.services.arcgis_ingestion import ingest_arcgis_zoning
    from app.services.fact_population import populate_parcel_zoning_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        summary = ingest_arcgis_zoning(db, jurisdiction.id)
        logger.info("arcgis_task.zoning.done", processed=summary.processed)

        fact_count = populate_parcel_zoning_facts(db, jurisdiction.id)
        logger.info("arcgis_task.zoning_facts.done", upserted=fact_count)

        return {
            "status": "completed",
            "zoning_processed": summary.processed,
            "zoning_failed": summary.failed,
            "zoning_facts_upserted": fact_count,
        }
    except Exception as e:
        logger.error("arcgis_task.zoning.failed", error=str(e))
        raise
    finally:
        db.close()


@celery.task(bind=True, max_retries=2)
def ingest_arcgis_constraints_task(self):
    """Phase 4: Ingest Toronto constraint overlays from ArcGIS."""
    from app.services.arcgis_ingestion import ingest_arcgis_constraints
    from app.services.fact_population import populate_parcel_constraint_facts

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        results = ingest_arcgis_constraints(db, jurisdiction.id)
        logger.info("arcgis_task.constraints.done")

        fact_count = populate_parcel_constraint_facts(db, jurisdiction.id)
        logger.info("arcgis_task.constraint_facts.done", upserted=fact_count)

        return {
            "status": "completed",
            "heritage_processed": results["heritage"].processed,
            "ravine_processed": results["ravine"].processed,
            "esa_processed": results["esa"].processed,
            "constraint_facts_upserted": fact_count,
        }
    except Exception as e:
        logger.error("arcgis_task.constraints.failed", error=str(e))
        raise
    finally:
        db.close()


@celery.task(bind=True, max_retries=1)
def ingest_arcgis_full_task(self):
    """Run all 4 ArcGIS ingestion phases sequentially."""
    from app.services.arcgis_ingestion import (
        ingest_arcgis_parcels,
        ingest_arcgis_addresses,
        ingest_arcgis_buildings,
        link_buildings_to_parcels,
        ingest_arcgis_zoning,
        ingest_arcgis_constraints,
    )
    from app.services.fact_population import (
        populate_parcel_current_facts,
        populate_parcel_building_facts,
        populate_parcel_zoning_facts,
        populate_parcel_constraint_facts,
    )

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(db, name="Toronto")
        db.commit()

        # Phase 1: Parcels + Addresses
        parcel_summary = ingest_arcgis_parcels(db, jurisdiction.id)
        addr_summary = ingest_arcgis_addresses(db, jurisdiction.id)
        current_facts = populate_parcel_current_facts(db, jurisdiction.id)

        # Phase 2: Buildings
        bld_summary = ingest_arcgis_buildings(db, jurisdiction.id)
        bld_links = link_buildings_to_parcels(db, jurisdiction.id)
        building_facts = populate_parcel_building_facts(db, jurisdiction.id)

        # Phase 3: Zoning
        zoning_summary = ingest_arcgis_zoning(db, jurisdiction.id)
        zoning_facts = populate_parcel_zoning_facts(db, jurisdiction.id)

        # Phase 4: Constraints
        constraint_results = ingest_arcgis_constraints(db, jurisdiction.id)
        constraint_facts = populate_parcel_constraint_facts(db, jurisdiction.id)

        return {
            "status": "completed",
            "phase1": {
                "parcels": parcel_summary.processed,
                "addresses": addr_summary.processed,
                "current_facts": current_facts,
            },
            "phase2": {
                "buildings": bld_summary.processed,
                "links": bld_links,
                "building_facts": building_facts,
            },
            "phase3": {
                "zoning": zoning_summary.processed,
                "zoning_facts": zoning_facts,
            },
            "phase4": {
                "heritage": constraint_results["heritage"].processed,
                "ravine": constraint_results["ravine"].processed,
                "esa": constraint_results["esa"].processed,
                "constraint_facts": constraint_facts,
            },
        }
    except Exception as e:
        logger.error("arcgis_task.full.failed", error=str(e))
        raise
    finally:
        db.close()
