"""Toronto ArcGIS FeatureServer ingestion — parcels, addresses, buildings, zoning, constraints."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from geoalchemy2 import WKTElement
from psycopg2.extras import execute_values
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.clients.arcgis_rest import iter_all_features, get_layer_metadata
from app.models.dataset import DatasetFeature, DatasetLayer
from app.services.geospatial_ingestion import (
    IngestionSummary,
    _coerce_float,
    _now,
    _append_issue,
    create_ingestion_job,
    create_snapshot,
    geojson_to_wkt,
    get_or_create_jurisdiction,
    publish_snapshot,
    _finalize_job,
)

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# ArcGIS layer references (City of Toronto FeatureServer)
# ---------------------------------------------------------------------------

# Parcels / addresses
PARCEL_SERVICE = "cot_geospatial27"
PARCEL_LAYER_ID = 36          # Property Boundaries
ADDRESS_LAYER_ID = 101        # Address Points

# Buildings
BUILDING_SERVICE = "cot_geospatial3"
BUILDING_LAYER_ID = 2         # Building Outline Polygon

# Zoning (all on cot_geospatial11)
ZONING_SERVICE = "cot_geospatial11"
ZONING_AREA_LAYER_ID = 3
HEIGHT_OVERLAY_LAYER_ID = 9
LOT_COVERAGE_OVERLAY_LAYER_ID = 10
POLICY_AREA_OVERLAY_LAYER_ID = 13
PARKING_ZONE_OVERLAY_LAYER_ID = 61

# Constraints
HERITAGE_LAYER_ID = 56        # cot_geospatial11
RAVINE_SERVICE = "cot_geospatial13"
RAVINE_LAYER_ID = 70
ESA_LAYER_ID = 50             # cot_geospatial11

BATCH_SIZE = 500
PROGRESS_EVERY = 5_000


def _content_hash_sample(features: list[dict], sample_size: int = 100) -> str:
    raw = str(sorted(str(f) for f in features[:sample_size]))
    return hashlib.sha256(raw.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# Phase 1: Parcels + Addresses
# ═══════════════════════════════════════════════════════════════════════════

def ingest_arcgis_parcels(db: Session, jurisdiction_id: uuid.UUID) -> IngestionSummary:
    """Fetch Toronto property boundaries from ArcGIS and batch-insert into parcels table."""
    logger.info("arcgis.parcels.starting")

    meta = get_layer_metadata(PARCEL_SERVICE, PARCEL_LAYER_ID)
    source_url = f"https://gis.toronto.ca/arcgis/rest/services/{PARCEL_SERVICE}/FeatureServer/{PARCEL_LAYER_ID}"

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type="arcgis_parcel_base",
        version_label=f"arcgis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        source_url=source_url,
        publisher="City of Toronto",
        file_hash=hashlib.sha256(source_url.encode()).hexdigest(),
        schema_version="arcgis-featureserver",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=source_url,
        source_snapshot_id=snapshot.id,
        job_type="arcgis_parcel_base",
    )
    db.commit()

    summary = IngestionSummary(issues=[])
    bind = db.get_bind()
    engine = getattr(bind, "engine", bind)
    raw_conn = engine.raw_connection()
    batch: list[tuple[Any, ...]] = []
    started_at = time.monotonic()

    try:
        with raw_conn.cursor() as cursor:
            for index, feature in enumerate(iter_all_features(PARCEL_SERVICE, PARCEL_LAYER_ID)):
                props = feature.get("properties") or {}
                geometry = feature.get("geometry")
                if not geometry:
                    summary.failed += 1
                    _append_issue(summary, {"row": index, "reason": "missing_geometry"})
                    continue

                # Extract PIN — try multiple field names
                pin = None
                for key in ("PARCELID", "PIN", "parcel_id", "OBJECTID"):
                    val = props.get(key)
                    if val not in (None, "", 0):
                        pin = str(val).strip()
                        break
                if not pin:
                    summary.failed += 1
                    _append_issue(summary, {"row": index, "reason": "missing_pin"})
                    continue

                # Address
                addr_parts = []
                addr_num = props.get("ADDRESS_NUMBER") or props.get("ADDR_NUM") or ""
                street = props.get("LINEAR_NAME_FULL") or props.get("STREET_NAME") or ""
                if addr_num:
                    addr_parts.append(str(addr_num).strip())
                if street:
                    addr_parts.append(str(street).strip())
                address = " ".join(addr_parts) if addr_parts else None

                lot_area = _coerce_float(props.get("STATEDAREA") or props.get("AREA") or props.get("Shape__Area"))
                frontage = _coerce_float(props.get("LOT_FRONTAGE_M") or props.get("FRONTAGE"))
                depth = _coerce_float(props.get("LOT_DEPTH_M") or props.get("DEPTH"))

                try:
                    wkt = geojson_to_wkt(geometry)
                except (ValueError, KeyError):
                    summary.failed += 1
                    _append_issue(summary, {"row": index, "reason": "bad_geometry"})
                    continue

                batch.append((
                    jurisdiction_id,
                    snapshot.id,
                    pin,
                    address,
                    wkt,
                    lot_area,
                    frontage,
                    depth,
                    None,  # current_use
                ))

                if len(batch) >= BATCH_SIZE:
                    inserted = _insert_parcel_batch(cursor, batch)
                    raw_conn.commit()
                    summary.processed += inserted
                    summary.failed += len(batch) - inserted
                    batch.clear()

                    if summary.processed % PROGRESS_EVERY < BATCH_SIZE:
                        elapsed = time.monotonic() - started_at
                        logger.info(
                            "arcgis.parcels.progress",
                            processed=summary.processed,
                            failed=summary.failed,
                            elapsed_s=round(elapsed, 1),
                        )

            # Flush remaining
            if batch:
                inserted = _insert_parcel_batch(cursor, batch)
                raw_conn.commit()
                summary.processed += inserted
                summary.failed += len(batch) - inserted

        publish_snapshot(db, snapshot, validation_summary=summary.as_json())
        _finalize_job(job, summary)
    except Exception as exc:
        raw_conn.rollback()
        summary.failed += 1
        _append_issue(summary, {"reason": "exception", "detail": str(exc)})
        _finalize_job(job, summary, error=str(exc))
        db.commit()
        raise
    finally:
        raw_conn.close()

    db.commit()
    logger.info("arcgis.parcels.completed", processed=summary.processed, failed=summary.failed)
    return summary


def _insert_parcel_batch(cursor: Any, rows: list[tuple[Any, ...]]) -> int:
    """Batch-insert parcels with ON CONFLICT DO NOTHING."""
    execute_values(
        cursor,
        """
        INSERT INTO parcels (
            jurisdiction_id, source_snapshot_id, pin, address,
            geom, lot_area_m2, lot_frontage_m, lot_depth_m, current_use
        )
        VALUES %s
        ON CONFLICT ON CONSTRAINT uq_parcels_jurisdiction_pin_snapshot DO NOTHING
        RETURNING 1
        """,
        rows,
        template="""(
            %s::uuid, %s::uuid, %s, %s,
            ST_SetSRID(ST_GeomFromText(%s), 4326),
            %s, %s, %s, %s
        )""",
        page_size=len(rows),
    )
    return len(cursor.fetchall())


def ingest_arcgis_addresses(db: Session, jurisdiction_id: uuid.UUID) -> IngestionSummary:
    """Fetch Toronto address points from ArcGIS and match to parcels via ST_Contains."""
    logger.info("arcgis.addresses.starting")

    source_url = f"https://gis.toronto.ca/arcgis/rest/services/{PARCEL_SERVICE}/FeatureServer/{ADDRESS_LAYER_ID}"

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type="arcgis_address_points",
        version_label=f"arcgis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        source_url=source_url,
        publisher="City of Toronto",
        file_hash=hashlib.sha256(source_url.encode()).hexdigest(),
        schema_version="arcgis-featureserver",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=source_url,
        source_snapshot_id=snapshot.id,
        job_type="arcgis_address_points",
    )
    db.commit()

    summary = IngestionSummary(issues=[])
    bind = db.get_bind()
    engine = getattr(bind, "engine", bind)
    raw_conn = engine.raw_connection()
    batch: list[tuple[Any, ...]] = []

    try:
        with raw_conn.cursor() as cursor:
            for index, feature in enumerate(iter_all_features(PARCEL_SERVICE, ADDRESS_LAYER_ID)):
                props = feature.get("properties") or {}
                geometry = feature.get("geometry")
                if not geometry or geometry.get("type") != "Point":
                    summary.failed += 1
                    continue

                # Build address text
                addr_num = str(props.get("ADDRESS_NUMBER") or props.get("CIVIC_NUM") or "").strip()
                street = str(props.get("LINEAR_NAME_FULL") or props.get("STREET_NAME") or "").strip()
                street_type = str(props.get("LINEAR_NAME_TYPE") or "").strip()
                street_dir = str(props.get("LINEAR_NAME_DIR") or "").strip()

                parts = [p for p in (addr_num, street, street_type, street_dir) if p]
                address_text = " ".join(parts)
                if not address_text:
                    summary.failed += 1
                    continue

                source_record_id = str(
                    props.get("ADDRESS_POINT_ID") or props.get("OBJECTID") or index
                )

                coords = geometry.get("coordinates", [])
                if len(coords) < 2:
                    summary.failed += 1
                    continue
                lon, lat = coords[0], coords[1]
                point_wkt = f"POINT ({lon} {lat})"

                batch.append((
                    snapshot.id,
                    source_record_id,
                    address_text,
                    point_wkt,
                    jurisdiction_id,
                ))

                if len(batch) >= BATCH_SIZE:
                    inserted = _insert_address_batch(cursor, batch)
                    raw_conn.commit()
                    summary.processed += inserted
                    batch.clear()

            if batch:
                inserted = _insert_address_batch(cursor, batch)
                raw_conn.commit()
                summary.processed += inserted

        publish_snapshot(db, snapshot, validation_summary=summary.as_json())
        _finalize_job(job, summary)
    except Exception as exc:
        raw_conn.rollback()
        summary.failed += 1
        _append_issue(summary, {"reason": "exception", "detail": str(exc)})
        _finalize_job(job, summary, error=str(exc))
        db.commit()
        raise
    finally:
        raw_conn.close()

    db.commit()
    logger.info("arcgis.addresses.completed", processed=summary.processed, failed=summary.failed)
    return summary


def _insert_address_batch(cursor: Any, rows: list[tuple[Any, ...]]) -> int:
    """Batch-insert address points matched to parcels via ST_Contains."""
    execute_values(
        cursor,
        """
        INSERT INTO parcel_addresses (
            parcel_id, source_snapshot_id, source_record_id,
            address_text, address_point_geom, match_method, match_confidence, is_canonical
        )
        SELECT
            p.id,
            v.snapshot_id::uuid,
            v.source_record_id,
            v.address_text,
            ST_SetSRID(ST_GeomFromText(v.point_wkt), 4326),
            'spatial_contains',
            0.9,
            false
        FROM (VALUES %s) AS v(snapshot_id, source_record_id, address_text, point_wkt, jurisdiction_id)
        JOIN parcels p ON p.jurisdiction_id = v.jurisdiction_id::uuid
            AND ST_Contains(p.geom, ST_SetSRID(ST_GeomFromText(v.point_wkt), 4326))
        ON CONFLICT DO NOTHING
        RETURNING 1
        """,
        rows,
        template="(%s, %s, %s, %s, %s)",
        page_size=len(rows),
    )
    return len(cursor.fetchall())


# ═══════════════════════════════════════════════════════════════════════════
# Phase 2: Building Footprints
# ═══════════════════════════════════════════════════════════════════════════

def ingest_arcgis_buildings(db: Session, jurisdiction_id: uuid.UUID) -> IngestionSummary:
    """Fetch Toronto building footprints from ArcGIS and insert as DatasetLayer/DatasetFeature."""
    logger.info("arcgis.buildings.starting")

    source_url = f"https://gis.toronto.ca/arcgis/rest/services/{BUILDING_SERVICE}/FeatureServer/{BUILDING_LAYER_ID}"

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type="arcgis_building_footprints",
        version_label=f"arcgis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        source_url=source_url,
        publisher="City of Toronto",
        file_hash=hashlib.sha256(source_url.encode()).hexdigest(),
        schema_version="arcgis-featureserver",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=source_url,
        source_snapshot_id=snapshot.id,
        job_type="arcgis_building_footprints",
    )

    layer = DatasetLayer(
        jurisdiction_id=jurisdiction_id,
        name="toronto_building_footprints",
        layer_type="building_footprint",
        source_url=source_url,
        source_snapshot_id=snapshot.id,
        publisher="City of Toronto",
        acquired_at=_now(),
        license_status="open",
        internal_storage_allowed=True,
    )
    db.add(layer)
    db.flush()
    db.commit()

    summary = IngestionSummary(issues=[])
    bind = db.get_bind()
    engine = getattr(bind, "engine", bind)
    raw_conn = engine.raw_connection()
    batch: list[tuple[Any, ...]] = []

    try:
        with raw_conn.cursor() as cursor:
            for index, feature in enumerate(iter_all_features(BUILDING_SERVICE, BUILDING_LAYER_ID)):
                props = feature.get("properties") or {}
                geometry = feature.get("geometry")
                if not geometry:
                    summary.failed += 1
                    continue

                try:
                    wkt = geojson_to_wkt(geometry)
                except (ValueError, KeyError):
                    summary.failed += 1
                    continue

                source_record_id = str(props.get("OBJECTID") or props.get("BLD_ID") or index)
                batch.append((str(layer.id), source_record_id, wkt, json.dumps(props)))
                summary.processed += 1

                if len(batch) >= BATCH_SIZE:
                    _insert_feature_batch(cursor, batch)
                    raw_conn.commit()
                    batch.clear()

                    if summary.processed % PROGRESS_EVERY < BATCH_SIZE:
                        logger.info("arcgis.buildings.progress", processed=summary.processed)

            if batch:
                _insert_feature_batch(cursor, batch)
                raw_conn.commit()

        publish_snapshot(db, snapshot, validation_summary=summary.as_json())
        _finalize_job(job, summary)
    except Exception as exc:
        raw_conn.rollback()
        _finalize_job(job, summary, error=str(exc))
        db.commit()
        raise
    finally:
        raw_conn.close()

    db.commit()
    logger.info("arcgis.buildings.completed", processed=summary.processed, failed=summary.failed)
    return summary


def _insert_feature_batch(cursor: Any, rows: list[tuple[Any, ...]]) -> None:
    """Batch-insert dataset_features using raw SQL for performance."""
    execute_values(
        cursor,
        """
        INSERT INTO dataset_features (id, dataset_layer_id, source_record_id, geom, attributes_json)
        VALUES %s
        ON CONFLICT DO NOTHING
        """,
        rows,
        template="""(
            gen_random_uuid(), %s::uuid, %s,
            ST_SetSRID(ST_GeomFromText(%s), 4326), %s::json
        )""",
        page_size=len(rows),
    )


def link_buildings_to_parcels(db: Session, jurisdiction_id: uuid.UUID) -> int:
    """Bulk spatial join: link building features to parcels via ST_Intersects."""
    logger.info("arcgis.buildings.linking")
    result = db.execute(text("""
        INSERT INTO feature_to_parcel_links (id, feature_id, parcel_id, relationship_type)
        SELECT gen_random_uuid(), df.id, p.id, 'intersects'
        FROM dataset_features df
        JOIN dataset_layers dl ON dl.id = df.dataset_layer_id
            AND dl.layer_type = 'building_footprint'
            AND dl.jurisdiction_id = CAST(:jid AS uuid)
        JOIN parcels p ON p.jurisdiction_id = CAST(:jid AS uuid)
            AND ST_Intersects(df.geom, p.geom)
        ON CONFLICT ON CONSTRAINT uq_feature_parcel_link DO NOTHING
        RETURNING 1
    """), {"jid": str(jurisdiction_id)})
    count = len(result.fetchall())
    db.commit()
    logger.info("arcgis.buildings.linked", links_created=count)
    return count


# ═══════════════════════════════════════════════════════════════════════════
# Phase 3: Zoning
# ═══════════════════════════════════════════════════════════════════════════

def ingest_arcgis_zoning(db: Session, jurisdiction_id: uuid.UUID) -> IngestionSummary:
    """Fetch zoning areas from ArcGIS, insert as DatasetFeature, then bulk spatial join to parcels."""
    logger.info("arcgis.zoning.starting")

    source_url = f"https://gis.toronto.ca/arcgis/rest/services/{ZONING_SERVICE}/FeatureServer/{ZONING_AREA_LAYER_ID}"

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type="arcgis_zoning",
        version_label=f"arcgis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        source_url=source_url,
        publisher="City of Toronto",
        file_hash=hashlib.sha256(source_url.encode()).hexdigest(),
        schema_version="arcgis-featureserver",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=source_url,
        source_snapshot_id=snapshot.id,
        job_type="arcgis_zoning",
    )

    layer = DatasetLayer(
        jurisdiction_id=jurisdiction_id,
        name="toronto_zoning_areas",
        layer_type="zoning",
        source_url=source_url,
        source_snapshot_id=snapshot.id,
        publisher="City of Toronto",
        acquired_at=_now(),
        license_status="open",
        internal_storage_allowed=True,
    )
    db.add(layer)
    db.flush()
    db.commit()

    summary = IngestionSummary(issues=[])
    bind = db.get_bind()
    engine = getattr(bind, "engine", bind)
    raw_conn = engine.raw_connection()
    batch: list[tuple[Any, ...]] = []

    ZONE_CODE_FIELDS = ("ZN_STRING", "ZN_ZONE", "GEN_ZONE", "ZONE_CODE", "zone_code")

    try:
        with raw_conn.cursor() as cursor:
            for index, feature in enumerate(iter_all_features(ZONING_SERVICE, ZONING_AREA_LAYER_ID)):
                props = feature.get("properties") or {}
                geometry = feature.get("geometry")
                if not geometry:
                    summary.failed += 1
                    continue

                zone_code = None
                for key in ZONE_CODE_FIELDS:
                    val = props.get(key)
                    if val not in (None, ""):
                        zone_code = str(val).strip()
                        break
                if not zone_code:
                    summary.failed += 1
                    _append_issue(summary, {"row": index, "reason": "missing_zone_code"})
                    continue

                try:
                    wkt = geojson_to_wkt(geometry)
                except (ValueError, KeyError):
                    summary.failed += 1
                    continue

                attributes = {**props, "zone_code": zone_code}
                source_record_id = str(props.get("OBJECTID") or index)
                batch.append((str(layer.id), source_record_id, wkt, json.dumps(attributes)))
                summary.processed += 1

                if len(batch) >= BATCH_SIZE:
                    _insert_feature_batch(cursor, batch)
                    raw_conn.commit()
                    batch.clear()

                    if summary.processed % PROGRESS_EVERY < BATCH_SIZE:
                        logger.info("arcgis.zoning.progress", processed=summary.processed)

            if batch:
                _insert_feature_batch(cursor, batch)
                raw_conn.commit()
    finally:
        raw_conn.close()

    # Lightweight zone_code assignment via centroid-in-polygon
    # (avoids disk-heavy intersection + assignments table on constrained Railway instances)
    layer_id_str = str(layer.id)
    jid_str = str(jurisdiction_id)

    logger.info("arcgis.zoning.assigning_zone_codes")
    db.execute(text("""
        UPDATE parcels p
        SET zone_code = df.attributes_json->>'zone_code'
        FROM dataset_features df
        WHERE df.dataset_layer_id = CAST(:layer_id AS uuid)
            AND ST_Contains(df.geom, ST_Centroid(p.geom))
            AND p.jurisdiction_id = CAST(:jid AS uuid)
    """), {"layer_id": layer_id_str, "jid": jid_str})
    db.commit()
    logger.info("arcgis.zoning.zone_codes_assigned")

    publish_snapshot(db, snapshot, validation_summary=summary.as_json())
    _finalize_job(job, summary)
    db.commit()
    logger.info("arcgis.zoning.completed", processed=summary.processed, failed=summary.failed)
    return summary


# ═══════════════════════════════════════════════════════════════════════════
# Phase 4: Constraint Overlays (Heritage, Ravine, ESA)
# ═══════════════════════════════════════════════════════════════════════════

def _ingest_constraint_layer(
    db: Session,
    jurisdiction_id: uuid.UUID,
    *,
    service_url: str,
    layer_id: int,
    layer_name: str,
    layer_type: str,
    snapshot_type: str,
    job_type: str,
) -> tuple[DatasetLayer, IngestionSummary]:
    """Generic constraint layer ingestion: fetch from ArcGIS, store as DatasetLayer + DatasetFeature."""
    full_url = f"https://gis.toronto.ca/arcgis/rest/services/{service_url}/FeatureServer/{layer_id}"

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type=snapshot_type,
        version_label=f"arcgis-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        source_url=full_url,
        publisher="City of Toronto",
        file_hash=hashlib.sha256(full_url.encode()).hexdigest(),
        schema_version="arcgis-featureserver",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=full_url,
        source_snapshot_id=snapshot.id,
        job_type=job_type,
    )

    layer = DatasetLayer(
        jurisdiction_id=jurisdiction_id,
        name=layer_name,
        layer_type=layer_type,
        source_url=full_url,
        source_snapshot_id=snapshot.id,
        publisher="City of Toronto",
        acquired_at=_now(),
        license_status="open",
        internal_storage_allowed=True,
    )
    db.add(layer)
    db.flush()
    db.commit()

    summary = IngestionSummary(issues=[])
    bind = db.get_bind()
    engine_obj = getattr(bind, "engine", bind)
    raw_conn = engine_obj.raw_connection()
    batch: list[tuple[Any, ...]] = []

    try:
        with raw_conn.cursor() as cursor:
            for index, feature in enumerate(iter_all_features(service_url, layer_id)):
                props = feature.get("properties") or {}
                geometry = feature.get("geometry")
                if not geometry:
                    summary.failed += 1
                    continue

                try:
                    wkt = geojson_to_wkt(geometry)
                except (ValueError, KeyError):
                    summary.failed += 1
                    continue

                source_record_id = str(props.get("OBJECTID") or index)
                batch.append((str(layer.id), source_record_id, wkt, json.dumps(props)))
                summary.processed += 1

                if len(batch) >= BATCH_SIZE:
                    _insert_feature_batch(cursor, batch)
                    raw_conn.commit()
                    batch.clear()

                    if summary.processed % PROGRESS_EVERY < BATCH_SIZE:
                        logger.info(f"arcgis.constraint.{layer_name}.progress", processed=summary.processed)

            if batch:
                _insert_feature_batch(cursor, batch)
                raw_conn.commit()
    finally:
        raw_conn.close()

    # Skip spatial join to feature_to_parcel_links (too disk-heavy on Railway).
    # Constraint facts will be computed directly from geometry instead.

    publish_snapshot(db, snapshot, validation_summary=summary.as_json())
    _finalize_job(job, summary)
    db.commit()

    return layer, summary


def ingest_arcgis_constraints(db: Session, jurisdiction_id: uuid.UUID) -> dict[str, IngestionSummary]:
    """Ingest all constraint overlay layers: heritage, ravine, ESA."""
    logger.info("arcgis.constraints.starting")
    results: dict[str, IngestionSummary] = {}

    # Heritage
    _, heritage_summary = _ingest_constraint_layer(
        db, jurisdiction_id,
        service_url=ZONING_SERVICE,
        layer_id=HERITAGE_LAYER_ID,
        layer_name="toronto_heritage_properties",
        layer_type="heritage",
        snapshot_type="arcgis_heritage",
        job_type="arcgis_heritage",
    )
    results["heritage"] = heritage_summary
    logger.info("arcgis.constraints.heritage.done", processed=heritage_summary.processed)

    # Ravine
    _, ravine_summary = _ingest_constraint_layer(
        db, jurisdiction_id,
        service_url=RAVINE_SERVICE,
        layer_id=RAVINE_LAYER_ID,
        layer_name="toronto_ravine_protection",
        layer_type="ravine",
        snapshot_type="arcgis_ravine",
        job_type="arcgis_ravine",
    )
    results["ravine"] = ravine_summary
    logger.info("arcgis.constraints.ravine.done", processed=ravine_summary.processed)

    # ESA
    _, esa_summary = _ingest_constraint_layer(
        db, jurisdiction_id,
        service_url=ZONING_SERVICE,
        layer_id=ESA_LAYER_ID,
        layer_name="toronto_esa",
        layer_type="esa",
        snapshot_type="arcgis_esa",
        job_type="arcgis_esa",
    )
    results["esa"] = esa_summary
    logger.info("arcgis.constraints.esa.done", processed=esa_summary.processed)

    logger.info("arcgis.constraints.completed")
    return results
