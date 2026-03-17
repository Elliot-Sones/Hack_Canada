"""Populate fact tables from enriched normalized data via SQL UPSERTs."""

from __future__ import annotations

import json
import uuid

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.zoning_parser import extract_zone_category, get_zone_standards, parse_zone_string

logger = structlog.get_logger()


def populate_parcel_current_facts(db: Session, jurisdiction_id: uuid.UUID) -> int:
    """UPSERT parcel_current_facts from parcels + parcel_addresses.

    Fills: canonical_address, pin, lot_area_m2, lot_frontage_m, lot_depth_m,
           current_use, zone_code.
    """
    logger.info("facts.parcel_current.starting")
    jid = str(jurisdiction_id)

    result = db.execute(text("""
        INSERT INTO parcel_current_facts (
            id, parcel_id, jurisdiction_id, canonical_address,
            pin, lot_area_m2, lot_frontage_m, lot_depth_m,
            current_use, zone_code, updated_at
        )
        SELECT
            gen_random_uuid(),
            p.id,
            p.jurisdiction_id,
            COALESCE(
                (SELECT pa.address_text
                 FROM parcel_addresses pa
                 WHERE pa.parcel_id = p.id AND pa.is_canonical = true
                 LIMIT 1),
                (SELECT pa.address_text
                 FROM parcel_addresses pa
                 WHERE pa.parcel_id = p.id
                 ORDER BY pa.created_at DESC
                 LIMIT 1),
                p.address
            ),
            p.pin,
            COALESCE(p.lot_area_m2, p.geom_area_m2),
            p.lot_frontage_m,
            p.lot_depth_m,
            p.current_use,
            p.zone_code,
            now()
        FROM parcels p
        WHERE p.jurisdiction_id = CAST(:jid AS uuid)
        ON CONFLICT ON CONSTRAINT uq_parcel_current_facts_parcel
        DO UPDATE SET
            canonical_address = EXCLUDED.canonical_address,
            pin = EXCLUDED.pin,
            lot_area_m2 = EXCLUDED.lot_area_m2,
            lot_frontage_m = EXCLUDED.lot_frontage_m,
            lot_depth_m = EXCLUDED.lot_depth_m,
            current_use = EXCLUDED.current_use,
            zone_code = EXCLUDED.zone_code,
            updated_at = now()
    """), {"jid": jid})

    count = result.rowcount
    db.commit()
    logger.info("facts.parcel_current.completed", upserted=count)
    return count


def populate_parcel_building_facts(db: Session, jurisdiction_id: uuid.UUID) -> int:
    """UPSERT parcel_building_facts by aggregating building footprints per parcel.

    Uses a temp table to pre-compute building areas (avoids temp-file spills on
    disk-constrained Railway instances).
    """
    logger.info("facts.parcel_building.starting")
    jid = str(jurisdiction_id)

    # Step 1: Pre-compute per-building area into a temp table (avoids giant sort/hash)
    db.execute(text("DROP TABLE IF EXISTS _tmp_bld_areas"))
    db.execute(text("""
        CREATE TEMP TABLE _tmp_bld_areas AS
        SELECT df.id AS feature_id,
               ST_Area(ST_Transform(df.geom, 3857)) AS area_m2
        FROM dataset_features df
        JOIN dataset_layers dl ON dl.id = df.dataset_layer_id
            AND dl.layer_type = 'building_footprint'
            AND dl.jurisdiction_id = CAST(:jid AS uuid)
    """), {"jid": jid})
    db.commit()
    logger.info("facts.parcel_building.areas_computed")

    # Step 2: Aggregate per parcel into another temp table
    db.execute(text("DROP TABLE IF EXISTS _tmp_bld_agg"))
    db.execute(text("""
        CREATE TEMP TABLE _tmp_bld_agg AS
        SELECT
            fpl.parcel_id,
            COUNT(DISTINCT fpl.feature_id) AS cnt,
            SUM(ba.area_m2) AS total_footprint_m2
        FROM feature_to_parcel_links fpl
        JOIN _tmp_bld_areas ba ON ba.feature_id = fpl.feature_id
        GROUP BY fpl.parcel_id
    """))
    db.execute(text("CREATE INDEX ON _tmp_bld_agg (parcel_id)"))
    db.commit()
    logger.info("facts.parcel_building.aggregated")

    # Step 3: UPSERT parcels with buildings in batches (disk-friendly)
    batch_size = 50_000
    count1 = 0
    offset = 0
    while True:
        r1 = db.execute(text("""
            INSERT INTO parcel_building_facts (
                id, parcel_id, building_count, total_building_footprint_m2,
                building_coverage_pct, vacant_lot_flag, underutilized_flag, updated_at
            )
            SELECT
                gen_random_uuid(),
                bld.parcel_id,
                bld.cnt,
                bld.total_footprint_m2,
                CASE
                    WHEN p.geom_area_m2 > 0
                    THEN ROUND((bld.total_footprint_m2 / p.geom_area_m2 * 100)::numeric, 2)
                    ELSE NULL
                END,
                false,
                CASE
                    WHEN p.geom_area_m2 > 0
                        AND (bld.total_footprint_m2 / p.geom_area_m2) < 0.15
                    THEN true
                    ELSE false
                END,
                now()
            FROM (SELECT * FROM _tmp_bld_agg ORDER BY parcel_id LIMIT :batch OFFSET :off) bld
            JOIN parcels p ON p.id = bld.parcel_id
            ON CONFLICT ON CONSTRAINT uq_parcel_building_facts_parcel
            DO UPDATE SET
                building_count = EXCLUDED.building_count,
                total_building_footprint_m2 = EXCLUDED.total_building_footprint_m2,
                building_coverage_pct = EXCLUDED.building_coverage_pct,
                vacant_lot_flag = EXCLUDED.vacant_lot_flag,
                underutilized_flag = EXCLUDED.underutilized_flag,
                updated_at = now()
        """), {"jid": jid, "batch": batch_size, "off": offset})
        rows = r1.rowcount
        db.commit()
        count1 += rows
        offset += batch_size
        logger.info("facts.parcel_building.batch", upserted_so_far=count1, offset=offset)
        if rows < batch_size:
            break
    logger.info("facts.parcel_building.with_buildings", upserted=count1)

    # Step 4: Vacant lots in batches
    count2 = 0
    while True:
        r2 = db.execute(text("""
            INSERT INTO parcel_building_facts (
                id, parcel_id, building_count, total_building_footprint_m2,
                building_coverage_pct, vacant_lot_flag, underutilized_flag, updated_at
            )
            SELECT
                gen_random_uuid(),
                p.id,
                0, NULL, NULL, true, false, now()
            FROM parcels p
            WHERE p.jurisdiction_id = CAST(:jid AS uuid)
                AND NOT EXISTS (
                    SELECT 1 FROM parcel_building_facts pbf WHERE pbf.parcel_id = p.id
                )
            LIMIT :batch
            ON CONFLICT ON CONSTRAINT uq_parcel_building_facts_parcel
            DO UPDATE SET
                building_count = 0,
                total_building_footprint_m2 = NULL,
                building_coverage_pct = NULL,
                vacant_lot_flag = true,
                underutilized_flag = false,
                updated_at = now()
        """), {"jid": jid, "batch": batch_size})
        rows = r2.rowcount
        db.commit()
        count2 += rows
        logger.info("facts.parcel_building.vacant_batch", upserted_so_far=count2)
        if rows < batch_size:
            break

    # Cleanup temp tables
    db.execute(text("DROP TABLE IF EXISTS _tmp_bld_areas"))
    db.execute(text("DROP TABLE IF EXISTS _tmp_bld_agg"))
    db.commit()

    total = count1 + count2
    logger.info("facts.parcel_building.completed", upserted=total, with_buildings=count1, vacant=count2)
    return total


def populate_parcel_zoning_facts(db: Session, jurisdiction_id: uuid.UUID) -> int:
    """UPSERT parcel_zoning_facts by parsing zone codes and looking up standards.

    For each parcel with a zone_code, parse_zone_string() + get_zone_standards()
    produces height, storeys, FSI, coverage, permitted uses.
    """
    logger.info("facts.parcel_zoning.starting")
    jid = str(jurisdiction_id)

    # Fetch distinct zone codes and their parcel IDs in batches
    rows = db.execute(text("""
        SELECT p.id AS parcel_id, p.zone_code
        FROM parcels p
        WHERE p.jurisdiction_id = CAST(:jid AS uuid)
            AND p.zone_code IS NOT NULL
            AND p.zone_code != ''
    """), {"jid": jid}).fetchall()

    # Pre-compute standards per zone_code to avoid repeated parsing
    zone_cache: dict[str, dict] = {}
    upserted = 0

    batch_values: list[tuple] = []
    for parcel_id, zone_code in rows:
        if zone_code not in zone_cache:
            try:
                components = parse_zone_string(zone_code)
                standards = get_zone_standards(components)
                zone_cache[zone_code] = {
                    "zone_family": extract_zone_category(zone_code),
                    "max_height_m": standards.max_height_m,
                    "max_storeys": standards.max_storeys,
                    "max_fsi": standards.max_fsi,
                    "max_lot_coverage_pct": standards.max_lot_coverage_pct,
                    "permitted_uses": standards.permitted_uses,
                    "warnings": None,
                }
            except ValueError:
                zone_cache[zone_code] = {
                    "zone_family": extract_zone_category(zone_code),
                    "max_height_m": None,
                    "max_storeys": None,
                    "max_fsi": None,
                    "max_lot_coverage_pct": None,
                    "permitted_uses": [],
                    "warnings": {"parse_error": f"Could not parse zone string: {zone_code}"},
                }

        std = zone_cache[zone_code]
        batch_values.append((
            str(parcel_id),
            zone_code,
            std["zone_family"],
            std["max_height_m"],
            std["max_storeys"],
            std["max_fsi"],
            std["max_lot_coverage_pct"],
            json.dumps(std["permitted_uses"]) if std["permitted_uses"] else None,
            json.dumps(std["warnings"]) if std["warnings"] else None,
        ))

        if len(batch_values) >= 1000:
            upserted += _upsert_zoning_fact_batch(db, batch_values)
            batch_values.clear()

    if batch_values:
        upserted += _upsert_zoning_fact_batch(db, batch_values)

    db.commit()
    logger.info("facts.parcel_zoning.completed", upserted=upserted)
    return upserted


def _upsert_zoning_fact_batch(db: Session, batch: list[tuple]) -> int:
    """Batch upsert zoning facts using raw SQL for performance."""
    from psycopg2.extras import execute_values

    bind = db.get_bind()
    engine = getattr(bind, "engine", bind)
    raw_conn = engine.raw_connection()
    try:
        with raw_conn.cursor() as cursor:
            execute_values(
                cursor,
                """
                INSERT INTO parcel_zoning_facts (
                    id, parcel_id, primary_zone_code, zone_family,
                    max_height_m, max_storeys, max_fsi, max_lot_coverage_pct,
                    permitted_use_groups_json, warnings_json, updated_at
                )
                VALUES %s
                ON CONFLICT ON CONSTRAINT uq_parcel_zoning_facts_parcel
                DO UPDATE SET
                    primary_zone_code = EXCLUDED.primary_zone_code,
                    zone_family = EXCLUDED.zone_family,
                    max_height_m = EXCLUDED.max_height_m,
                    max_storeys = EXCLUDED.max_storeys,
                    max_fsi = EXCLUDED.max_fsi,
                    max_lot_coverage_pct = EXCLUDED.max_lot_coverage_pct,
                    permitted_use_groups_json = EXCLUDED.permitted_use_groups_json,
                    warnings_json = EXCLUDED.warnings_json,
                    updated_at = now()
                RETURNING 1
                """,
                batch,
                template="""(
                    gen_random_uuid(), %s::uuid, %s, %s,
                    %s, %s, %s, %s,
                    %s::jsonb, %s::jsonb, now()
                )""",
                page_size=len(batch),
            )
            count = len(cursor.fetchall())
        raw_conn.commit()
        return count
    finally:
        raw_conn.close()


def populate_parcel_constraint_facts(db: Session, jurisdiction_id: uuid.UUID) -> int:
    """UPSERT parcel_constraint_facts via direct spatial queries (disk-friendly).

    Uses temp tables to pre-compute which parcels intersect each constraint layer,
    then batches the final UPSERT to avoid disk pressure.
    """
    logger.info("facts.parcel_constraint.starting")
    jid = str(jurisdiction_id)

    # Pre-compute constraint flags into temp tables (small result sets)
    for layer_type, tmp_name in [("heritage", "_tmp_heritage"), ("ravine", "_tmp_ravine"), ("esa", "_tmp_esa")]:
        db.execute(text(f"DROP TABLE IF EXISTS {tmp_name}"))
        db.execute(text(f"""
            CREATE TEMP TABLE {tmp_name} AS
            SELECT DISTINCT p.id AS parcel_id
            FROM parcels p
            JOIN dataset_features df ON ST_Intersects(df.geom, p.geom)
            JOIN dataset_layers dl ON dl.id = df.dataset_layer_id
                AND dl.layer_type = :lt
                AND dl.jurisdiction_id = CAST(:jid AS uuid)
            WHERE p.jurisdiction_id = CAST(:jid AS uuid)
        """), {"lt": layer_type, "jid": jid})
        db.execute(text(f"CREATE INDEX ON {tmp_name} (parcel_id)"))
        cnt = db.execute(text(f"SELECT COUNT(*) FROM {tmp_name}")).fetchone()[0]
        db.commit()
        logger.info(f"facts.constraint.{layer_type}", parcels_affected=cnt)

    # Batch UPSERT constraint facts
    batch_size = 50_000
    total = 0
    offset = 0
    while True:
        r = db.execute(text("""
            INSERT INTO parcel_constraint_facts (
                id, parcel_id, heritage_flag, floodplain_flag, ravine_flag, esa_flag,
                overlay_count, floodplain_coverage_pct, updated_at
            )
            SELECT
                gen_random_uuid(),
                p.id,
                COALESCE(h.parcel_id IS NOT NULL, false),
                false,
                COALESCE(rv.parcel_id IS NOT NULL, false),
                COALESCE(e.parcel_id IS NOT NULL, false),
                (CASE WHEN h.parcel_id IS NOT NULL THEN 1 ELSE 0 END
                 + CASE WHEN rv.parcel_id IS NOT NULL THEN 1 ELSE 0 END
                 + CASE WHEN e.parcel_id IS NOT NULL THEN 1 ELSE 0 END),
                NULL,
                now()
            FROM (SELECT id FROM parcels WHERE jurisdiction_id = CAST(:jid AS uuid) ORDER BY id LIMIT :batch OFFSET :off) p
            LEFT JOIN _tmp_heritage h ON h.parcel_id = p.id
            LEFT JOIN _tmp_ravine rv ON rv.parcel_id = p.id
            LEFT JOIN _tmp_esa e ON e.parcel_id = p.id
            ON CONFLICT ON CONSTRAINT uq_parcel_constraint_facts_parcel
            DO UPDATE SET
                heritage_flag = EXCLUDED.heritage_flag,
                ravine_flag = EXCLUDED.ravine_flag,
                esa_flag = EXCLUDED.esa_flag,
                overlay_count = EXCLUDED.overlay_count,
                updated_at = now()
        """), {"jid": jid, "batch": batch_size, "off": offset})
        rows = r.rowcount
        db.commit()
        total += rows
        offset += batch_size
        logger.info("facts.constraint.batch", upserted_so_far=total)
        if rows < batch_size:
            break

    # Cleanup
    db.execute(text("DROP TABLE IF EXISTS _tmp_heritage"))
    db.execute(text("DROP TABLE IF EXISTS _tmp_ravine"))
    db.execute(text("DROP TABLE IF EXISTS _tmp_esa"))
    db.commit()

    logger.info("facts.parcel_constraint.completed", upserted=total)
    return total
