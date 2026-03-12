"""Water main ingestion service.

Ingests Toronto distribution water mains from local GeoJSON into the
`pipeline_assets` table with `pipe_type = 'water_main'`.

Only distribution mains are relevant for development feasibility —
transmission mains, hydrants, valves, fittings, and parks drinking water
are dropped (developers connect to distribution, not trunk mains; the
rest is utility-operations data reviewed by other agencies).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# Material normalisation
# ---------------------------------------------------------------------------

MATERIAL_ALIASES: dict[str, str] = {
    "DI": "DI", "DIP": "DI", "DUCTILE IRON": "DI", "DUCTILEIRON": "DI",
    "CI": "CI", "CIP": "CI", "CAST IRON": "CI", "CASTIRON": "CI",
    "GI": "CI", "GALV": "CI",
    "PVC": "PVC", "POLYVINYL": "PVC",
    "HDPE": "HDPE", "PE": "HDPE", "POLYETHYLENE": "HDPE",
    "CPP": "RCP", "RCP": "RCP", "CONCRETE": "RCP", "RC": "RCP", "PCCP": "RCP",
    "STE": "STEEL", "STEEL": "STEEL", "ST": "STEEL",
    "AC": "AC", "ACP": "AC", "ASBESTOS": "AC", "ASBESTOS CEMENT": "AC",
    "CSP": "CSP",
    "COP": "COPPER", "COPPER": "COPPER",
}

VALID_STATUSES = {"ACTIVE", "ABANDONED", "PROPOSED", "INACTIVE", "UNKNOWN"}


def _normalise_material(raw: str | None) -> str:
    if not raw:
        return "UNKNOWN"
    return MATERIAL_ALIASES.get(str(raw).strip().upper(), "UNKNOWN")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(props: dict, *keys: str, default=None) -> Any:
    """Try multiple key variants (original / UPPER / lower)."""
    for key in keys:
        for variant in (key, key.upper(), key.lower()):
            val = props.get(variant)
            if val is not None and str(val) not in ("", "None", "null"):
                return val
    return default


def _safe_int(val) -> int | None:
    try:
        return int(float(val)) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> float | None:
    try:
        return round(float(val), 4) if val is not None else None
    except (ValueError, TypeError):
        return None


def _safe_year(val) -> int | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        year = int(val)
        return year if 1800 <= year <= 2100 else None
    if isinstance(val, str) and len(val) >= 4:
        try:
            year = int(val[:4])
            return year if 1800 <= year <= 2100 else None
        except ValueError:
            pass
    return None


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def _valid_line(geom: dict | None) -> bool:
    if not geom:
        return False
    t = geom.get("type", "")
    c = geom.get("coordinates", [])
    if t == "LineString":
        return len(c) >= 2
    if t == "MultiLineString":
        return any(len(line) >= 2 for line in c)
    return False


def _geojson_to_ewkt(geom: dict) -> str:
    t = geom["type"]
    c = geom["coordinates"]
    if t == "LineString":
        interior = "(" + ",".join(f"{p[0]} {p[1]}" for p in c) + ")"
        return f"LINESTRING{interior}"
    if t == "MultiLineString":
        parts = ["(" + ",".join(f"{p[0]} {p[1]}" for p in line) + ")" for line in c]
        return "MULTILINESTRING(" + ",".join(parts) + ")"
    raise ValueError(f"Unsupported geometry type: {t}")


# ---------------------------------------------------------------------------
# Feature streaming
# ---------------------------------------------------------------------------

def _stream_features(path: Path) -> Iterator[dict]:
    try:
        import ijson
        with open(path, "rb") as f:
            yield from ijson.items(f, "features.item")
    except ImportError:
        import json
        with open(path) as f:
            data = json.load(f)
        yield from data.get("features", [])


# ---------------------------------------------------------------------------
# Core ingestion — writes directly to pipeline_assets
# ---------------------------------------------------------------------------

def ingest_distribution_watermains(
    db: Session,
    *,
    jurisdiction_id: uuid.UUID,
    geojson_path: Path,
    version_label: str,
    source_url: str,
    publisher: str,
    batch_size: int = 1000,
    feature_iterator: Iterator[dict] | None = None,
) -> tuple[Any, Any]:
    """Ingest distribution water mains into pipeline_assets."""
    from app.models.infrastructure import PipelineAsset
    from app.models.ingestion import IngestionJob, SourceSnapshot

    now = datetime.now(timezone.utc)

    snapshot = SourceSnapshot(
        id=uuid.uuid4(),
        jurisdiction_id=jurisdiction_id,
        snapshot_type="water_main_distribution",
        version_label=version_label,
        is_active=True,
        created_at=now,
    )
    db.add(snapshot)
    db.flush()

    job = IngestionJob(
        id=uuid.uuid4(),
        jurisdiction_id=jurisdiction_id,
        source_snapshot_id=snapshot.id,
        source_url=source_url,
        job_type="water_main_distribution_ingest",
        status="running",
        records_processed=0,
        records_failed=0,
        started_at=now,
    )
    db.add(job)
    db.commit()

    iterator = feature_iterator or _stream_features(geojson_path)
    batch: list[PipelineAsset] = []
    processed = failed = 0

    def _flush():
        if batch:
            db.bulk_save_objects(batch)
            db.flush()
            batch.clear()

    try:
        for raw in iterator:
            geom = raw.get("geometry")
            props = raw.get("properties") or {}

            if not _valid_line(geom):
                failed += 1
                continue

            raw_material = _get(props, "Watermain Material", "MATERIAL", "PIPE_MAT")
            raw_install = _get(props, "Watermain Install Date", "INSTALL_YR")
            raw_year = _get(props, "Watermain Construction Year", "INSTALL_YR")

            material = _normalise_material(raw_material)
            diameter_mm = _safe_int(_get(props, "Watermain Diameter", "DIAMETER", "DIA_MM"))
            install_year = _safe_year(raw_install) or _safe_year(raw_year)
            length_m = _safe_float(_get(props, "Watermain Measured Length", "Shape_Length", "LENGTH_M"))
            location_desc = str(_get(props, "Watermain Location Description") or "")
            pressure_zone = str(_get(props, "PRESSURE_ZONE", "PRES_ZONE") or "")
            asset_id = str(_get(props, "Watermain Asset Identification", "WATMAIN_ID") or "")

            batch.append(PipelineAsset(
                id=uuid.uuid4(),
                jurisdiction_id=jurisdiction_id,
                source_snapshot_id=snapshot.id,
                asset_id=asset_id,
                pipe_type="water_main",
                material=material,
                diameter_mm=float(diameter_mm) if diameter_mm else None,
                install_year=install_year,
                depth_m=None,
                slope_pct=None,
                length_m=length_m,
                location_desc=location_desc or None,
                status="ACTIVE",
                geom=f"SRID=4326;{_geojson_to_ewkt(geom)}",
                attributes_json={
                    "pressure_zone": pressure_zone,
                    "material_raw": str(raw_material or ""),
                },
            ))
            processed += 1

            if len(batch) >= batch_size:
                _flush()
                print(f"\r    {processed:,} water main features ingested...", end="", flush=True)

        _flush()
        print(f"\r    {processed:,} water main features ingested.     ")
        if failed:
            print(f"    {failed:,} features skipped (no valid geometry)")

        job.status = "completed"
        job.records_processed = processed
        job.records_failed = failed
        job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as exc:
        db.rollback()
        job.status = "failed"
        job.records_processed = processed
        job.records_failed = failed + 1
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise

    return snapshot, job


# ---------------------------------------------------------------------------
# Convenience: seed all water layers
# ---------------------------------------------------------------------------

WATER_LAYER_MANIFEST = [
    (ingest_distribution_watermains, "watermain-distribution-4326.geojson", "water-mains", "Distribution water mains"),
]


def seed_all_water_layers(
    db: Session,
    *,
    jurisdiction_id: uuid.UUID,
    data_dir: Path,
    version_label: str,
    publisher: str = "City of Toronto",
    source_base: str = "https://open.toronto.ca/dataset",
    batch_size: int = 1000,
) -> dict[str, dict]:
    """Seed distribution water mains from staged data_dir."""
    results = {}
    for fn, filename, url_suffix, description in WATER_LAYER_MANIFEST:
        path = data_dir / filename
        if not path.exists():
            print(f"  SKIP {description} — {filename} not found in {data_dir}")
            continue
        print(f"\n  [{description}]")
        size_mb = path.stat().st_size / (1024 * 1024)
        print(f"    File: {filename} ({size_mb:.1f} MB)")
        snap, job = fn(
            db,
            jurisdiction_id=jurisdiction_id,
            geojson_path=path,
            version_label=version_label,
            source_url=f"{source_base}/{url_suffix}",
            publisher=publisher,
            batch_size=batch_size,
        )
        results[job.job_type] = {
            "snapshot_id": str(snap.id),
            "processed": job.records_processed,
            "failed": job.records_failed,
            "status": job.status,
        }
    return results
