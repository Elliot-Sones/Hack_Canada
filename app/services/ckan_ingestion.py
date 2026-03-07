"""CKAN Open Data ingestion for Toronto building permits and COA applications."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import httpx
import structlog
from geoalchemy2 import WKTElement
from pyproj import Transformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entitlement import BuildingPermit, DevelopmentApplication
from app.services.geospatial_ingestion import (
    IngestionSummary,
    _coerce_float,
    _now,
    create_ingestion_job,
    create_snapshot,
    get_or_create_jurisdiction,
    publish_snapshot,
    _finalize_job,
)

logger = structlog.get_logger()

CKAN_BASE = "https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action"
CKAN_PAGE_SIZE = 100

# UTM Zone 17N → WGS84
_utm_transformer = Transformer.from_crs("EPSG:26917", "EPSG:4326", always_xy=True)


def _parse_date(value: Any) -> datetime | None:
    """Parse a date string from CKAN into a date object."""
    if not value or value in ("", "null", "None"):
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%m/%d/%Y", "%d-%b-%Y"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _discover_resource_id(package_name: str) -> str:
    """Discover the datastore resource_id for a CKAN package (sync HTTP)."""
    url = f"{CKAN_BASE}/package_show"
    resp = httpx.get(url, params={"id": package_name}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    resources = data.get("result", {}).get("resources", [])
    # Pick the first datastore-active resource
    for r in resources:
        if r.get("datastore_active"):
            return r["id"]
    # Fallback: first resource
    if resources:
        return resources[0]["id"]
    raise ValueError(f"No resources found for CKAN package: {package_name}")


def _fetch_ckan_records(resource_id: str) -> list[dict[str, Any]]:
    """Fetch all records from a CKAN datastore resource, handling pagination."""
    all_records: list[dict[str, Any]] = []
    offset = 0
    while True:
        resp = httpx.get(
            f"{CKAN_BASE}/datastore_search",
            params={"resource_id": resource_id, "limit": CKAN_PAGE_SIZE, "offset": offset},
            timeout=60,
        )
        resp.raise_for_status()
        result = resp.json().get("result", {})
        records = result.get("records", [])
        if not records:
            break
        all_records.extend(records)
        offset += len(records)
        # Stop if we got fewer than a full page
        if len(records) < CKAN_PAGE_SIZE:
            break
    return all_records


def _content_hash(records: list[dict]) -> str:
    """Compute a hash of the fetched records for snapshot tracking."""
    raw = str(sorted(str(r) for r in records[:100]))
    return hashlib.sha256(raw.encode()).hexdigest()


def ingest_building_permits(
    db: Session,
    jurisdiction_id: uuid.UUID,
) -> IngestionSummary:
    """Fetch building permits from Toronto CKAN and upsert into building_permits table."""
    logger.info("ckan.building_permits.starting")
    resource_id = _discover_resource_id("building-permits-active")
    records = _fetch_ckan_records(resource_id)
    logger.info("ckan.building_permits.fetched", count=len(records))

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type="building_permits_ckan",
        version_label=f"ckan-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        source_url=f"{CKAN_BASE}/datastore_search?resource_id={resource_id}",
        publisher="City of Toronto Open Data",
        file_hash=_content_hash(records),
        schema_version="ckan-datastore",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=f"{CKAN_BASE}/datastore_search?resource_id={resource_id}",
        source_snapshot_id=snapshot.id,
        job_type="building_permits_ckan",
    )

    summary = IngestionSummary(issues=[])
    seen: set[str] = set()

    for idx, rec in enumerate(records):
        permit_number = rec.get("PERMIT_NUM") or rec.get("PERMIT_NUMBER")
        if not permit_number:
            summary.failed += 1
            summary.issues.append({"row": idx, "reason": "missing_permit_number"})
            continue
        permit_number = str(permit_number).strip()
        if permit_number in seen:
            continue
        seen.add(permit_number)

        # Check for existing permit (dedup via unique constraint)
        existing = db.execute(
            select(BuildingPermit).where(
                BuildingPermit.jurisdiction_id == jurisdiction_id,
                BuildingPermit.permit_number == permit_number,
            )
        ).scalar_one_or_none()
        if existing:
            summary.processed += 1
            continue

        # Build address
        parts = [
            str(rec.get("STREET_NUM") or "").strip(),
            str(rec.get("STREET_NAME") or "").strip(),
            str(rec.get("STREET_TYPE") or "").strip(),
            str(rec.get("STREET_DIRECTION") or "").strip(),
        ]
        address = " ".join(p for p in parts if p) or None

        # Geometry from lat/lon if available
        point_geom = None
        lat = _coerce_float(rec.get("LATITUDE") or rec.get("Y"))
        lon = _coerce_float(rec.get("LONGITUDE") or rec.get("X"))
        if lat is not None and lon is not None:
            point_geom = WKTElement(f"POINT ({lon} {lat})", srid=4326)

        permit = BuildingPermit(
            jurisdiction_id=jurisdiction_id,
            permit_number=permit_number,
            permit_type=rec.get("PERMIT_TYPE") or "unknown",
            status=rec.get("STATUS") or "unknown",
            address=address,
            source_system="toronto_ckan_permits",
            application_date=_parse_date(rec.get("APPLICATION_DATE")),
            issue_date=_parse_date(rec.get("ISSUED_DATE")),
            closed_date=_parse_date(rec.get("COMPLETED_DATE")),
            geom=point_geom,
            metadata_json={
                k: v for k, v in rec.items()
                if k not in {
                    "PERMIT_NUM", "PERMIT_NUMBER", "PERMIT_TYPE", "STATUS",
                    "STREET_NUM", "STREET_NAME", "STREET_TYPE", "STREET_DIRECTION",
                    "APPLICATION_DATE", "ISSUED_DATE", "COMPLETED_DATE",
                    "LATITUDE", "LONGITUDE", "X", "Y", "_id",
                }
            },
        )
        db.add(permit)
        summary.processed += 1

    publish_snapshot(db, snapshot, validation_summary=summary.as_json())
    _finalize_job(job, summary)
    db.commit()

    logger.info("ckan.building_permits.completed", processed=summary.processed, failed=summary.failed)
    return summary


def ingest_coa_applications(
    db: Session,
    jurisdiction_id: uuid.UUID,
) -> IngestionSummary:
    """Fetch Committee of Adjustment applications from Toronto CKAN and upsert into development_applications."""
    logger.info("ckan.coa_applications.starting")
    resource_id = _discover_resource_id("committee-of-adjustment-applications")
    records = _fetch_ckan_records(resource_id)
    logger.info("ckan.coa_applications.fetched", count=len(records))

    snapshot = create_snapshot(
        db,
        jurisdiction_id=jurisdiction_id,
        snapshot_type="coa_applications_ckan",
        version_label=f"ckan-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        source_url=f"{CKAN_BASE}/datastore_search?resource_id={resource_id}",
        publisher="City of Toronto Open Data",
        file_hash=_content_hash(records),
        schema_version="ckan-datastore",
    )
    job = create_ingestion_job(
        db,
        jurisdiction_id=jurisdiction_id,
        source_url=f"{CKAN_BASE}/datastore_search?resource_id={resource_id}",
        source_snapshot_id=snapshot.id,
        job_type="coa_applications_ckan",
    )

    summary = IngestionSummary(issues=[])
    seen: set[str] = set()

    for idx, rec in enumerate(records):
        app_number = rec.get("APPLICATION_NUMBER") or rec.get("APPLICATION_NUM")
        if not app_number:
            summary.failed += 1
            summary.issues.append({"row": idx, "reason": "missing_app_number"})
            continue
        app_number = str(app_number).strip()
        if app_number in seen:
            continue
        seen.add(app_number)

        # Check for existing (dedup via unique constraint)
        existing = db.execute(
            select(DevelopmentApplication).where(
                DevelopmentApplication.jurisdiction_id == jurisdiction_id,
                DevelopmentApplication.app_number == app_number,
            )
        ).scalar_one_or_none()
        if existing:
            # Update decision if we now have one and it was previously NULL
            decision_raw = rec.get("DECISION")
            if decision_raw and not existing.decision:
                existing.decision = str(decision_raw).strip()
            if not existing.decision_date:
                existing.decision_date = _parse_date(rec.get("DECISION_DATE"))
            summary.processed += 1
            continue

        # Build address
        parts = [
            str(rec.get("STREET_NUM") or rec.get("STREET_NUMBER") or "").strip(),
            str(rec.get("STREET_NAME") or "").strip(),
            str(rec.get("STREET_TYPE") or "").strip(),
        ]
        address = " ".join(p for p in parts if p) or None

        # Decision
        decision = rec.get("DECISION")
        if decision:
            decision = str(decision).strip()

        # Ward
        ward_raw = rec.get("WARD") or rec.get("WARD_NAME")
        ward = str(ward_raw).strip() if ward_raw else None

        # Geometry: COA data may use UTM Zone 17N (X/Y) coordinates
        point_geom = None
        x_raw = _coerce_float(rec.get("X") or rec.get("LONGITUDE"))
        y_raw = _coerce_float(rec.get("Y") or rec.get("LATITUDE"))
        if x_raw is not None and y_raw is not None:
            # Determine if UTM or already WGS84
            if x_raw > 1000:
                # UTM coordinates
                lon, lat = _utm_transformer.transform(x_raw, y_raw)
            else:
                lon, lat = x_raw, y_raw
            point_geom = WKTElement(f"POINT ({lon} {lat})", srid=4326)

        # Parse description for height/units
        description = rec.get("DESCRIPTION") or rec.get("APPLICATION_DESCRIPTION") or ""
        proposed_units = None
        proposed_height_m = None
        proposed_storeys = None

        storey_match = re.search(r"(\d+)[- ]?storey", description, re.IGNORECASE)
        if storey_match:
            proposed_storeys = int(storey_match.group(1))
            proposed_height_m = float(proposed_storeys * 3)

        unit_match = re.search(
            r"(\d[\d,]*)\s*(?:residential\s+)?(?:units?|dwelling)", description, re.IGNORECASE
        )
        if unit_match:
            proposed_units = int(unit_match.group(1).replace(",", ""))

        metadata = {
            k: v for k, v in rec.items()
            if k not in {
                "APPLICATION_NUMBER", "APPLICATION_NUM", "APPLICATION_TYPE",
                "STATUS", "DECISION", "STREET_NUM", "STREET_NUMBER",
                "STREET_NAME", "STREET_TYPE", "WARD", "WARD_NAME",
                "SUBMITTED_DATE", "DECISION_DATE", "X", "Y",
                "LONGITUDE", "LATITUDE", "DESCRIPTION",
                "APPLICATION_DESCRIPTION", "_id",
            }
        }

        dev_app = DevelopmentApplication(
            jurisdiction_id=jurisdiction_id,
            app_number=app_number,
            source_system="toronto_ckan_coa",
            address=address,
            geom=point_geom,
            app_type=rec.get("APPLICATION_TYPE") or "Minor Variance",
            status=rec.get("STATUS") or "unknown",
            decision=decision,
            ward=ward,
            submitted_at=_parse_date(rec.get("SUBMITTED_DATE")),
            decision_date=_parse_date(rec.get("DECISION_DATE")),
            proposed_units=proposed_units,
            proposed_height_m=proposed_height_m,
            publisher="City of Toronto Open Data",
            acquired_at=_now(),
            source_schema_version="ckan-datastore",
            metadata_json=metadata,
        )
        db.add(dev_app)
        summary.processed += 1

    publish_snapshot(db, snapshot, validation_summary=summary.as_json())
    _finalize_job(job, summary)
    db.commit()

    logger.info("ckan.coa_applications.completed", processed=summary.processed, failed=summary.failed)
    return summary
