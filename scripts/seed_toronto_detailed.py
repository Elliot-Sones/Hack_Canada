"""Seed all Toronto Open Data files in one shot.

Usage:
    python scripts/seed_toronto.py --data-dir data/
    python scripts/seed_toronto.py --data-dir data/ --skip-steps 2 --batch-size 5000
    python scripts/seed_toronto.py --data-dir data/ --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import settings
from app.database import get_sync_db
from app.devtools import (
    redact_connection_url,
    render_preflight_checks,
    run_preflight_checks,
    raise_for_failed_checks,
)
from app.services.geospatial_ingestion import (
    get_or_create_jurisdiction,
    ingest_development_applications,
    ingest_overlay_geojson,
    ingest_parcel_geojson,
    ingest_zoning_geojson,
    link_address_file,
    resolve_active_snapshot_id,
)

logger = logging.getLogger("seed_toronto")

PUBLISHER = "City of Toronto"
SOURCE_BASE = "https://open.toronto.ca"

# ---------------------------------------------------------------------------
# Source URL registry — every dataset we know about
# ---------------------------------------------------------------------------
SOURCES = {
    "parcels": f"{SOURCE_BASE}/dataset/property-boundaries",
    "addresses": f"{SOURCE_BASE}/dataset/address-points-municipal-toronto-one-address-repository",
    "zoning_areas": f"{SOURCE_BASE}/dataset/zoning-by-law-569-2013-area",
    "height_overlay": f"{SOURCE_BASE}/dataset/zoning-by-law-569-2013-height-overlay",
    "setback_overlay": f"{SOURCE_BASE}/dataset/zoning-by-law-569-2013-setback-overlay",
    "lot_coverage_overlay": f"{SOURCE_BASE}/dataset/zoning-by-law-569-2013-lot-coverage-overlay",
    "rooming_house_overlay": f"{SOURCE_BASE}/dataset/zoning-by-law-569-2013-rooming-house-overlay",
    "dev_applications": f"{SOURCE_BASE}/dataset/development-applications",
    "site_plan_applications": f"{SOURCE_BASE}/dataset/site-plan-applications",
    "minor_variance": f"{SOURCE_BASE}/dataset/committee-of-adjustment-minor-variance-decisions",
    "consent_applications": f"{SOURCE_BASE}/dataset/committee-of-adjustment-consent-applications",
    "building_permits": f"{SOURCE_BASE}/dataset/building-permits-active-permits",
    "heritage_properties": f"{SOURCE_BASE}/dataset/heritage-register",
    "ravine_protection": f"{SOURCE_BASE}/dataset/ravine-and-natural-feature-protection",
    "flood_plain": f"{SOURCE_BASE}/dataset/flood-plain",
    "greenbelts": f"{SOURCE_BASE}/dataset/greenbelt",
    "tree_canopy": f"{SOURCE_BASE}/dataset/street-tree-data",
    "transit_routes": f"{SOURCE_BASE}/dataset/ttc-routes-and-schedules",
    "neighbourhoods": f"{SOURCE_BASE}/dataset/neighbourhoods",
    "ward_boundaries": f"{SOURCE_BASE}/dataset/city-wards",
}

# ---------------------------------------------------------------------------
# File candidate lists — we check multiple naming conventions
# ---------------------------------------------------------------------------
ADDRESS_FILE_CANDIDATES = (
    "address-points-4326.geojson",
    "address-points-4326.csv",
    "address_points_4326.geojson",
    "address_points_4326.csv",
    "address-points.geojson",
    "address-points.csv",
    "address_points.geojson",
    "address_points.csv",
    "Address Points - Municipal - Toronto One Address Repository.geojson",
)

# Maps a logical layer name to a list of filenames we'll look for (first match wins)
OVERLAY_FILE_CANDIDATES: dict[str, list[str]] = {
    "lot_coverage_overlay": [
        "zoning-lot-coverage-overlay-4326.geojson",
        "zoning_lot_coverage_overlay_4326.geojson",
        "zoning-lot-coverage-overlay.geojson",
    ],
    "rooming_house_overlay": [
        "zoning-rooming-house-overlay-4326.geojson",
        "zoning_rooming_house_overlay_4326.geojson",
        "zoning-rooming-house-overlay.geojson",
    ],
}

SUPPLEMENTARY_FILE_CANDIDATES: dict[str, list[str]] = {
    "site_plan_applications": [
        "site-plan-applications.json",
        "site_plan_applications.json",
    ],
    "minor_variance": [
        "minor-variance-decisions.json",
        "minor_variance_decisions.json",
        "committee-of-adjustment-minor-variance.json",
    ],
    "consent_applications": [
        "consent-applications.json",
        "consent_applications.json",
    ],
    "building_permits": [
        "building-permits-active.json",
        "building_permits_active.json",
        "building-permits.json",
        "building_permits.json",
    ],
    "heritage_properties": [
        "heritage-register-4326.geojson",
        "heritage_register_4326.geojson",
        "heritage-register.geojson",
    ],
    "ravine_protection": [
        "ravine-protection-4326.geojson",
        "ravine_protection_4326.geojson",
        "ravine-protection.geojson",
    ],
    "flood_plain": [
        "flood-plain-4326.geojson",
        "flood_plain_4326.geojson",
        "flood-plain.geojson",
    ],
    "neighbourhoods": [
        "neighbourhoods-4326.geojson",
        "neighbourhoods_4326.geojson",
        "neighbourhoods.geojson",
    ],
    "ward_boundaries": [
        "city-wards-4326.geojson",
        "city_wards_4326.geojson",
        "city-wards.geojson",
    ],
}

# The files that MUST exist for the core pipeline to run
REQUIRED_DATA_FILES = (
    "property-boundaries-4326.geojson",
    "zoning-area-4326.geojson",
    "zoning-height-overlay-4326.geojson",
    "zoning-building-setback-overlay-4326.geojson",
    "development-applications.json",
)

# Overlay descriptors used in the main pipeline
OVERLAY_LAYER_META: dict[str, dict[str, str]] = {
    "height_overlay": {
        "file": "zoning-height-overlay-4326.geojson",
        "layer_name": "Toronto Height Overlay",
        "layer_type": "height_overlay",
        "source_key": "height_overlay",
    },
    "setback_overlay": {
        "file": "zoning-building-setback-overlay-4326.geojson",
        "layer_name": "Toronto Building Setback Overlay",
        "layer_type": "setback_overlay",
        "source_key": "setback_overlay",
    },
    "lot_coverage_overlay": {
        "file": None,  # resolved via candidates
        "layer_name": "Toronto Lot Coverage Overlay",
        "layer_type": "lot_coverage_overlay",
        "source_key": "lot_coverage_overlay",
    },
    "rooming_house_overlay": {
        "file": None,
        "layer_name": "Toronto Rooming House Overlay",
        "layer_type": "rooming_house_overlay",
        "source_key": "rooming_house_overlay",
    },
}


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------
@dataclass
class StepResult:
    label: str
    step_number: int
    snapshot_id: int | None = None
    records_processed: int = 0
    records_failed: int = 0
    status: str = "skipped"
    elapsed_seconds: float = 0.0
    error: str | None = None


@dataclass
class SeedReport:
    results: list[StepResult] = field(default_factory=list)

    def add(self, result: StepResult) -> None:
        self.results.append(result)

    @property
    def total_processed(self) -> int:
        return sum(r.records_processed for r in self.results)

    @property
    def total_failed(self) -> int:
        return sum(r.records_failed for r in self.results)

    @property
    def any_errors(self) -> bool:
        return any(r.error is not None for r in self.results)

    def render(self) -> str:
        lines = [
            "",
            "=" * 72,
            "  TORONTO SEED — SUMMARY",
            "=" * 72,
        ]
        for r in self.results:
            status_icon = "✓" if r.status == "completed" else ("⊘" if r.status == "skipped" else "✗")
            line = (
                f"  {status_icon} [{r.step_number:>2}] {r.label:<35} "
                f"processed={r.records_processed:<8} failed={r.records_failed:<6} "
                f"{r.elapsed_seconds:>6.1f}s"
            )
            if r.error:
                line += f"  ERROR: {r.error[:60]}"
            lines.append(line)
        lines.append("-" * 72)
        lines.append(f"  Total processed: {self.total_processed}   Total failed: {self.total_failed}")
        lines.append("=" * 72)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_file(data_dir: Path, candidates: list[str] | tuple[str, ...]) -> Path | None:
    """Return the first file that exists from a list of candidates."""
    for candidate in candidates:
        path = data_dir / candidate
        if path.exists():
            return path
    return None


def _resolve_address_file(data_dir: Path, explicit_path: Path | None) -> Path | None:
    if explicit_path is not None:
        return explicit_path
    return _resolve_file(data_dir, ADDRESS_FILE_CANDIDATES)


def _count_geojson_features(path: Path) -> int | None:
    """Quickly count features in a GeoJSON file without full parsing."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
        features = data.get("features", [])
        return len(features)
    except Exception:
        return None


def _count_json_records(path: Path) -> int | None:
    """Count records in a JSON file (expecting a list at top level or under a key)."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return len(data)
        # Some Toronto datasets nest records under a key
        for key in ("records", "data", "features", "results"):
            if key in data and isinstance(data[key], list):
                return len(data[key])
        return None
    except Exception:
        return None


def _validate_geojson_crs(path: Path) -> str | None:
    """Check that a GeoJSON file has the expected CRS (EPSG:4326) or warn."""
    try:
        with open(path, "r") as f:
            # Read only the first 4KB to find the CRS without parsing everything
            head = f.read(4096)
        if "4326" in head or "WGS 84" in head or '"crs"' not in head:
            return None  # OK — 4326 or no CRS specified (defaults to 4326)
        return f"CRS in {path.name} may not be EPSG:4326 — geometries could be incorrect"
    except Exception:
        return None


def _print_result(label: str, snapshot: Any, job: Any) -> None:
    print(
        f"  {label}: snapshot={snapshot.id}  "
        f"processed={job.records_processed}  failed={job.records_failed}  status={job.status}"
    )


def _timed(fn, *args, **kwargs) -> tuple[Any, float]:
    """Run *fn* and return (result, elapsed_seconds)."""
    t0 = time.monotonic()
    result = fn(*args, **kwargs)
    return result, time.monotonic() - t0


# ---------------------------------------------------------------------------
# Ingestion steps
# ---------------------------------------------------------------------------
def _ingest_parcels(
    db, jid: int, data_dir: Path, args: argparse.Namespace, report: SeedReport, step: int
) -> int | None:
    """Step: Property boundaries (parcels). Returns parcel_snapshot_id."""
    label = "parcels"
    path = data_dir / "property-boundaries-4326.geojson"
    feature_count = _count_geojson_features(path)
    if feature_count is not None:
        print(f"       (source contains {feature_count:,} features)")

    crs_warning = _validate_geojson_crs(path)
    if crs_warning:
        logger.warning(crs_warning)

    try:
        (snap, job), elapsed = _timed(
            ingest_parcel_geojson,
            db,
            jurisdiction_id=jid,
            geojson_path=path,
            version_label=args.version_label,
            source_url=SOURCES["parcels"],
            publisher=PUBLISHER,
        )
        _print_result(label, snap, job)

        result = StepResult(
            label=label,
            step_number=step,
            snapshot_id=snap.id,
            records_processed=job.records_processed,
            records_failed=job.records_failed,
            status=job.status,
            elapsed_seconds=elapsed,
        )

        if feature_count is not None and job.records_processed < feature_count:
            gap = feature_count - job.records_processed
            logger.warning(
                f"Parcel ingestion gap: {gap:,} features in source not processed "
                f"({job.records_processed:,}/{feature_count:,}). "
                f"Check for null geometries or invalid features."
            )
            result.error = f"{gap} features not ingested"

        report.add(result)
        return resolve_active_snapshot_id(db, jurisdiction_id=jid, snapshot_type="parcel_base")

    except Exception as exc:
        logger.exception("Failed to ingest parcels")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        raise


def _link_addresses(
    db,
    jid: int,
    parcel_snapshot_id: int | None,
    data_dir: Path,
    args: argparse.Namespace,
    report: SeedReport,
    step: int,
) -> None:
    """Step: Link address points to parcels."""
    label = "address linkage"
    address_file = _resolve_address_file(data_dir, args.address_file)

    if address_file is None:
        print("  address linkage: skipped — no address-points file found in data directory")
        report.add(StepResult(label=label, step_number=step, status="skipped"))
        return

    if parcel_snapshot_id is None:
        logger.warning("Cannot link addresses without a parcel snapshot")
        report.add(
            StepResult(label=label, step_number=step, status="skipped", error="no parcel snapshot available")
        )
        return

    feature_count = _count_geojson_features(address_file) if address_file.suffix == ".geojson" else None
    if feature_count is not None:
        print(f"       (source contains {feature_count:,} address points)")

    try:
        (snap, job), elapsed = _timed(
            link_address_file,
            db,
            jurisdiction_id=jid,
            parcel_snapshot_id=parcel_snapshot_id,
            source_path=address_file,
            version_label=args.version_label,
            source_url=SOURCES["addresses"],
            publisher=PUBLISHER,
        )
        _print_result(label, snap, job)
        result = StepResult(
            label=label,
            step_number=step,
            snapshot_id=snap.id,
            records_processed=job.records_processed,
            records_failed=job.records_failed,
            status=job.status,
            elapsed_seconds=elapsed,
        )
        if feature_count is not None and job.records_processed < feature_count * 0.9:
            result.error = f"Only {job.records_processed:,}/{feature_count:,} addresses linked"
            logger.warning(result.error)
        report.add(result)

    except Exception as exc:
        logger.exception("Failed to link addresses")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        if not args.continue_on_error:
            raise


def _ingest_zoning(
    db,
    jid: int,
    parcel_snapshot_id: int | None,
    data_dir: Path,
    args: argparse.Namespace,
    report: SeedReport,
    step: int,
) -> None:
    """Step: Zoning areas."""
    label = "zoning"
    path = data_dir / "zoning-area-4326.geojson"
    feature_count = _count_geojson_features(path)
    if feature_count is not None:
        print(f"       (source contains {feature_count:,} features)")

    try:
        (snap, job), elapsed = _timed(
            ingest_zoning_geojson,
            db,
            jurisdiction_id=jid,
            parcel_snapshot_id=parcel_snapshot_id,
            geojson_path=path,
            version_label=args.version_label,
            source_url=SOURCES["zoning_areas"],
            publisher=PUBLISHER,
        )
        _print_result(label, snap, job)
        result = StepResult(
            label=label,
            step_number=step,
            snapshot_id=snap.id,
            records_processed=job.records_processed,
            records_failed=job.records_failed,
            status=job.status,
            elapsed_seconds=elapsed,
        )
        if feature_count is not None and job.records_processed < feature_count:
            gap = feature_count - job.records_processed
            result.error = f"{gap} zoning features not ingested"
            logger.warning(result.error)
        report.add(result)

    except Exception as exc:
        logger.exception("Failed to ingest zoning areas")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        if not args.continue_on_error:
            raise


def _ingest_overlay(
    db,
    jid: int,
    data_dir: Path,
    args: argparse.Namespace,
    report: SeedReport,
    step: int,
    overlay_key: str,
) -> None:
    """Step: Ingest a single overlay layer."""
    meta = OVERLAY_LAYER_META[overlay_key]
    label = meta["layer_name"]

    # Resolve file path
    if meta["file"] is not None:
        path = data_dir / meta["file"]
    else:
        candidates = OVERLAY_FILE_CANDIDATES.get(overlay_key, [])
        path = _resolve_file(data_dir, candidates)

    if path is None or not path.exists():
        print(f"  {label}: skipped — file not found")
        report.add(StepResult(label=label, step_number=step, status="skipped", error="file not found"))
        return

    feature_count = _count_geojson_features(path)
    if feature_count is not None:
        print(f"       (source contains {feature_count:,} features)")

    try:
        (snap, job), elapsed = _timed(
            ingest_overlay_geojson,
            db,
            jurisdiction_id=jid,
            geojson_path=path,
            version_label=args.version_label,
            source_url=SOURCES[meta["source_key"]],
            layer_name=meta["layer_name"],
            layer_type=meta["layer_type"],
            publisher=PUBLISHER,
        )
        _print_result(label, snap, job)
        result = StepResult(
            label=label,
            step_number=step,
            snapshot_id=snap.id,
            records_processed=job.records_processed,
            records_failed=job.records_failed,
            status=job.status,
            elapsed_seconds=elapsed,
        )
        if feature_count is not None and job.records_processed < feature_count:
            gap = feature_count - job.records_processed
            result.error = f"{gap} overlay features not ingested"
            logger.warning(result.error)
        report.add(result)

    except Exception as exc:
        logger.exception(f"Failed to ingest overlay: {label}")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        if not args.continue_on_error:
            raise


def _ingest_dev_applications(
    db,
    jid: int,
    parcel_snapshot_id: int | None,
    data_dir: Path,
    args: argparse.Namespace,
    report: SeedReport,
    step: int,
) -> None:
    """Step: Development applications."""
    label = "dev applications"
    path = data_dir / "development-applications.json"
    record_count = _count_json_records(path)
    if record_count is not None:
        print(f"       (source contains {record_count:,} records)")

    try:
        (snap, job), elapsed = _timed(
            ingest_development_applications,
            db,
            jurisdiction_id=jid,
            json_path=path,
            version_label=args.version_label,
            source_url=SOURCES["dev_applications"],
            publisher=PUBLISHER,
            parcel_snapshot_id=parcel_snapshot_id,
        )
        _print_result(label, snap, job)
        result = StepResult(
            label=label,
            step_number=step,
            snapshot_id=snap.id,
            records_processed=job.records_processed,
            records_failed=job.records_failed,
            status=job.status,
            elapsed_seconds=elapsed,
        )
        if record_count is not None and job.records_processed < record_count:
            gap = record_count - job.records_processed
            result.error = f"{gap} dev application records not ingested"
            logger.warning(result.error)
        report.add(result)

    except Exception as exc:
        logger.exception("Failed to ingest development applications")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        if not args.continue_on_error:
            raise


def _ingest_supplementary_json(
    db,
    jid: int,
    parcel_snapshot_id: int | None,
    data_dir: Path,
    args: argparse.Namespace,
    report: SeedReport,
    step: int,
    dataset_key: str,
    label: str,
) -> None:
    """Step: Ingest a supplementary JSON-based dataset (site plans, minor variances, etc.)."""
    candidates = SUPPLEMENTARY_FILE_CANDIDATES.get(dataset_key, [])
    path = _resolve_file(data_dir, candidates)

    if path is None:
        print(f"  {label}: skipped — file not found")
        report.add(StepResult(label=label, step_number=step, status="skipped", error="file not found"))
        return

    record_count = _count_json_records(path)
    if record_count is not None:
        print(f"       (source contains {record_count:,} records)")

    try:
        (snap, job), elapsed = _timed(
            ingest_development_applications,
            db,
            jurisdiction_id=jid,
            json_path=path,
            version_label=args.version_label,
            source_url=SOURCES.get(dataset_key, f"{SOURCE_BASE}/dataset/{dataset_key}"),
            publisher=PUBLISHER,
            parcel_snapshot_id=parcel_snapshot_id,
        )
        _print_result(label, snap, job)
        report.add(
            StepResult(
                label=label,
                step_number=step,
                snapshot_id=snap.id,
                records_processed=job.records_processed,
                records_failed=job.records_failed,
                status=job.status,
                elapsed_seconds=elapsed,
            )
        )
    except Exception as exc:
        logger.exception(f"Failed to ingest {label}")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        if not args.continue_on_error:
            raise


def _ingest_supplementary_geojson(
    db,
    jid: int,
    data_dir: Path,
    args: argparse.Namespace,
    report: SeedReport,
    step: int,
    dataset_key: str,
    label: str,
    layer_type: str,
) -> None:
    """Step: Ingest a supplementary GeoJSON overlay dataset."""
    candidates = SUPPLEMENTARY_FILE_CANDIDATES.get(dataset_key, [])
    path = _resolve_file(data_dir, candidates)

    if path is None:
        print(f"  {label}: skipped — file not found")
        report.add(StepResult(label=label, step_number=step, status="skipped", error="file not found"))
        return

    feature_count = _count_geojson_features(path)
    if feature_count is not None:
        print(f"       (source contains {feature_count:,} features)")

    try:
        (snap, job), elapsed = _timed(
            ingest_overlay_geojson,
            db,
            jurisdiction_id=jid,
            geojson_path=path,
            version_label=args.version_label,
            source_url=SOURCES.get(dataset_key, f"{SOURCE_BASE}/dataset/{dataset_key}"),
            layer_name=label,
            layer_type=layer_type,
            publisher=PUBLISHER,
        )
        _print_result(label, snap, job)
        report.add(
            StepResult(
                label=label,
                step_number=step,
                snapshot_id=snap.id,
                records_processed=job.records_processed,
                records_failed=job.records_failed,
                status=job.status,
                elapsed_seconds=elapsed,
            )
        )
    except Exception as exc:
        logger.exception(f"Failed to ingest {label}")
        report.add(StepResult(label=label, step_number=step, status="error", error=str(exc)[:200]))
        if not args.continue_on_error:
            raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Toronto Open Data into Arterial")
    parser.add_argument("--data-dir", required=True, type=Path, help="Directory containing downloaded data files")
    parser.add_argument("--jurisdiction-name", default="Toronto")
    parser.add_argument("--province", default="Ontario")
    parser.add_argument("--country", default="CA")
    parser.add_argument("--version-label", default="toronto-open-data-2024")
    parser.add_argument("--address-file", type=Path, default=None, help="Optional Toronto address-points GeoJSON/CSV")
    parser.add_argument(
        "--skip-steps",
        type=int,
        nargs="*",
        default=[],
        help="Step numbers to skip (e.g. --skip-steps 2 7 8)",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        default=False,
        help="Continue with remaining steps if one fails",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Validate files and show plan without writing to database",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    data_dir = args.data_dir

    # Build required paths — only the core 5 files are strictly required
    required_paths = [data_dir / filename for filename in REQUIRED_DATA_FILES]
    if args.address_file is not None:
        required_paths.append(args.address_file)

    print(f"Database target: {redact_connection_url(settings.DATABASE_URL_SYNC)}")
    print(f"Data directory:  {data_dir.resolve()}")
    print()

    # --- Discovery: show what files we found --------------------------------
    print("Discovered data files:")
    all_candidates: dict[str, Path | None] = {}
    all_candidates["address_points"] = _resolve_address_file(data_dir, args.address_file)
    for key, cands in OVERLAY_FILE_CANDIDATES.items():
        all_candidates[key] = _resolve_file(data_dir, cands)
    for key, cands in SUPPLEMENTARY_FILE_CANDIDATES.items():
        all_candidates[key] = _resolve_file(data_dir, cands)
    for req_file in REQUIRED_DATA_FILES:
        p = data_dir / req_file
        tag = "✓" if p.exists() else "✗"
        print(f"  {tag} {req_file}")
    for key, resolved in all_candidates.items():
        if resolved is not None:
            print(f"  ✓ {key} → {resolved.name}")
        else:
            print(f"  · {key} → (not found, will skip)")
    print()

    # --- Preflight ----------------------------------------------------------
    checks = run_preflight_checks(required_paths=required_paths)
    print(render_preflight_checks(checks))
    try:
        raise_for_failed_checks(checks)
    except RuntimeError as exc:
        raise SystemExit(f"Preflight failed: {exc}") from exc

    # --- CRS validation -----------------------------------------------------
    geojson_files = [data_dir / f for f in REQUIRED_DATA_FILES if f.endswith(".geojson")]
    for gf in geojson_files:
        warning = _validate_geojson_crs(gf)
        if warning:
            logger.warning(warning)

    if args.dry_run:
        print("DRY RUN — no data will be written. Exiting.")
        return

    # --- Ingestion ----------------------------------------------------------
    skip = set(args.skip_steps)
    report = SeedReport()
    step_counter = 0

    db = get_sync_db()
    try:
        jurisdiction = get_or_create_jurisdiction(
            db, name=args.jurisdiction_name, province=args.province, country=args.country
        )
        jid = jurisdiction.id
        parcel_snapshot_id: int | None = None

        # Step 1 — Property boundaries (parcels)
        step_counter += 1
        if step_counter not in skip:
            print(f"[{step_counter}] Ingesting property boundaries ...")
            parcel_snapshot_id = _ingest_parcels(db, jid, data_dir, args, report, step_counter)
        else:
            print(f"[{step_counter}] Ingesting property boundaries ... SKIPPED")
            report.add(StepResult(label="parcels", step_number=step_counter, status="skipped"))
            # Try to resolve an existing parcel snapshot anyway
            try:
                parcel_snapshot_id = resolve_active_snapshot_id(db, jurisdiction_id=jid, snapshot_type="parcel_base")
            except Exception:
                logger.warning("No existing parcel snapshot found — address/zoning linkage may fail")

        # Step 2 — Address points
        step_counter += 1
        if step_counter not in skip:
            print(f"[{step_counter}] Linking address points ...")
            _link_addresses(db, jid, parcel_snapshot_id, data_dir, args, report, step_counter)
        else:
            print(f"[{step_counter}] Linking address points ... SKIPPED")
            report.add(StepResult(label="address linkage", step_number=step_counter, status="skipped"))

        # Step 3 — Zoning areas
        step_counter += 1
        if step_counter not in skip:
            print(f"[{step_counter}] Ingesting zoning areas ...")
            _ingest_zoning(db, jid, parcel_snapshot_id, data_dir, args, report, step_counter)
        else:
            print(f"[{step_counter}] Ingesting zoning areas ... SKIPPED")
            report.add(StepResult(label="zoning", step_number=step_counter, status="skipped"))

        # Steps 4+ — Overlays (height, setback, lot coverage, rooming house)
        for overlay_key in ("height_overlay", "setback_overlay", "lot_coverage_overlay", "rooming_house_overlay"):
            step_counter += 1
            meta = OVERLAY_LAYER_META[overlay_key]
            if step_counter not in skip:
                print(f"[{step_counter}] Ingesting {meta['layer_name']} ...")
                _ingest_overlay(db, jid, data_dir, args, report, step_counter, overlay_key)
            else:
                print(f"[{step_counter}] Ingesting {meta['layer_name']} ... SKIPPED")
                report.add(StepResult(label=meta["layer_name"], step_number=step_counter, status="skipped"))

        # Step — Development applications
        step_counter += 1
        if step_counter not in skip:
            print(f"[{step_counter}] Ingesting development applications ...")
            _ingest_dev_applications(db, jid, parcel_snapshot_id, data_dir, args, report, step_counter)
        else:
            print(f"[{step_counter}] Ingesting development applications ... SKIPPED")
            report.add(StepResult(label="dev applications", step_number=step_counter, status="skipped"))

        # Supplementary JSON datasets
        supplementary_json_datasets = [
            ("site_plan_applications", "Site Plan Applications"),
            ("minor_variance", "Minor Variance Decisions"),
            ("consent_applications", "Consent Applications"),
            ("building_permits", "Building Permits (Active)"),
        ]
        for ds_key, ds_label in supplementary_json_datasets:
            step_counter += 1
            if step_counter not in skip:
                print(f"[{step_counter}] Ingesting {ds_label} ...")
                _ingest_supplementary_json(
                    db, jid, parcel_snapshot_id, data_dir, args, report, step_counter, ds_key, ds_label
                )
            else:
                print(f"[{step_counter}] Ingesting {ds_label} ... SKIPPED")
                report.add(StepResult(label=ds_label, step_number=step_counter, status="skipped"))

        # Supplementary GeoJSON datasets
        supplementary_geojson_datasets = [
            ("heritage_properties", "Heritage Register", "heritage_overlay"),
            ("ravine_protection", "Ravine & Natural Feature Protection", "environmental_overlay"),
            ("flood_plain", "Flood Plain", "environmental_overlay"),
            ("neighbourhoods", "Neighbourhoods", "boundary_overlay"),
            ("ward_boundaries", "City Wards", "boundary_overlay"),
        ]
        for ds_key, ds_label, ds_layer_type in supplementary_geojson_datasets:
            step_counter += 1
            if step_counter not in skip:
                print(f"[{step_counter}] Ingesting {ds_label} ...")
                _ingest_supplementary_geojson(
                    db, jid, data_dir, args, report, step_counter, ds_key, ds_label, ds_layer_type
                )
            else:
                print(f"[{step_counter}] Ingesting {ds_label} ... SKIPPED")
                report.add(StepResult(label=ds_label, step_number=step_counter, status="skipped"))

        # --- Summary --------------------------------------------------------
        print(report.render())

        if report.any_errors:
            logger.warning("Some steps had errors — review the summary above")
            sys.exit(1)

        print("\nDone — Toronto seed run completed successfully.")

    except Exception:
        db.rollback()
        print(report.render())
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()