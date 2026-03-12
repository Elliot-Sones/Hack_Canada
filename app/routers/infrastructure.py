"""Infrastructure endpoints — nearby assets and compliance checks.

Returns GeoJSON FeatureCollections so the map can render infrastructure layers directly.
All queries hit typed DB tables (pipeline_assets, electrical_assets) — no file caches.
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.schemas.infrastructure import PipelineComplianceRequest, ElectricalComplianceRequest, CapacityCheckRequest
from app.services.infrastructure_compliance import check_pipeline_compliance
from app.services.electrical_capacity import check_capacity as run_capacity_check
from app.data.electrical_standards import VOLTAGE_TIERS

router = APIRouter()

# Pipe-type → hex color for map rendering
PIPE_COLORS = {
    "water_main": "#2277bb",
    "sanitary_sewer": "#886644",
    "storm_sewer": "#44aa66",
    "gas_line": "#ddaa22",
}

# Electrical colors
ELECTRICAL_COLORS = {
    "power_line": "#e74c3c",
    "electrical_substation": "#8e44ad",
}


def _voltage_tier_color(tier: str | None) -> tuple[str, float]:
    """Return (color, line_width_factor) for a voltage tier key."""
    if tier and tier in VOLTAGE_TIERS:
        t = VOLTAGE_TIERS[tier]
        return t["color"], t["line_width_factor"]
    t = VOLTAGE_TIERS["unknown"]
    return t["color"], t["line_width_factor"]


# ─── Pipeline Endpoints ──────────────────────────────────────────────────────


@router.get("/infrastructure/pipelines/nearby")
async def get_nearby_pipelines(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(default=500, ge=1, le=10000),
    pipe_type: str | None = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Return pipeline assets as a GeoJSON FeatureCollection."""
    point_wkt = f"SRID=4326;POINT({lng} {lat})"
    type_filter = "AND pipe_type = :pipe_type" if pipe_type else ""
    result = await db.execute(
        text(f"""
            SELECT id, asset_id, pipe_type, material, diameter_mm,
                   install_year, depth_m, slope_pct, length_m, location_desc, status,
                   attributes_json,
                   ST_AsGeoJSON(geom)::json AS geometry,
                   ST_Distance(geom::geography, ST_GeomFromEWKT(:point)::geography) AS distance_m
            FROM pipeline_assets
            WHERE ST_DWithin(geom::geography, ST_GeomFromEWKT(:point)::geography, :radius)
              AND geom IS NOT NULL
              {type_filter}
            ORDER BY distance_m
            LIMIT 200
        """),
        {"point": point_wkt, "radius": radius_m, **({"pipe_type": pipe_type} if pipe_type else {})},
    )
    rows = result.mappings().all()
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "id": str(row["id"]),
                "asset_id": row["asset_id"],
                "pipe_type": row["pipe_type"],
                "material": row["material"],
                "diameter_mm": row["diameter_mm"],
                "install_year": row["install_year"],
                "depth_m": row["depth_m"],
                "slope_pct": row["slope_pct"],
                "length_m": row["length_m"],
                "location": row["location_desc"],
                "status": row["status"],
                "distance_m": round(row["distance_m"], 1) if row["distance_m"] else None,
                "color": PIPE_COLORS.get(row["pipe_type"], "#888888"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/infrastructure/watermains/bbox")
async def get_watermains_bbox(
    min_lng: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lng: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    limit: int = Query(default=3000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db_session),
):
    """Return water main segments within a map viewport bbox from pipeline_assets."""
    result = await db.execute(
        text("""
            SELECT asset_id, pipe_type, material, diameter_mm, install_year,
                   length_m, location_desc, depth_m, status,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM pipeline_assets
            WHERE pipe_type = 'water_main'
              AND ST_Intersects(geom, ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326))
            LIMIT :limit
        """),
        {"min_lng": min_lng, "min_lat": min_lat, "max_lng": max_lng, "max_lat": max_lat, "limit": limit},
    )
    rows = result.mappings().all()
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "asset_id": row["asset_id"],
                "pipe_type": row["pipe_type"],
                "material": row["material"],
                "diameter_mm": row["diameter_mm"],
                "install_year": row["install_year"],
                "length_m": row["length_m"],
                "location": row["location_desc"],
                "depth_m": row["depth_m"],
                "status": row["status"],
                "color": PIPE_COLORS["water_main"],
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/infrastructure/sewers/bbox")
async def get_sewers_bbox(
    min_lng: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lng: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    pipe_type: str | None = Query(default=None, description="Filter: sanitary_sewer or storm_sewer"),
    limit: int = Query(default=3000, ge=1, le=10000),
    db: AsyncSession = Depends(get_db_session),
):
    """Return sewer segments within a map viewport bbox from pipeline_assets."""
    if pipe_type and pipe_type not in ("sanitary_sewer", "storm_sewer"):
        pipe_type = None

    type_filter = "AND pipe_type = :pipe_type" if pipe_type else "AND pipe_type IN ('sanitary_sewer', 'storm_sewer')"
    result = await db.execute(
        text(f"""
            SELECT asset_id, pipe_type, material, diameter_mm, install_year,
                   length_m, location_desc, depth_m, slope_pct, status,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM pipeline_assets
            WHERE ST_Intersects(geom, ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326))
              {type_filter}
            LIMIT :limit
        """),
        {
            "min_lng": min_lng, "min_lat": min_lat, "max_lng": max_lng, "max_lat": max_lat,
            "limit": limit,
            **({"pipe_type": pipe_type} if pipe_type else {}),
        },
    )
    rows = result.mappings().all()
    features = []
    for row in rows:
        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "asset_id": row["asset_id"],
                "pipe_type": row["pipe_type"],
                "material": row["material"],
                "diameter_mm": row["diameter_mm"],
                "install_year": row["install_year"],
                "length_m": row["length_m"],
                "location": row["location_desc"],
                "depth_m": row["depth_m"],
                "slope_pct": row["slope_pct"],
                "status": row["status"],
                "color": PIPE_COLORS.get(row["pipe_type"], "#888888"),
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.post("/infrastructure/compliance/pipeline")
async def check_pipeline(
    body: PipelineComplianceRequest,
    user: dict = Depends(get_current_user),
):
    """Run deterministic compliance check for a pipeline."""
    params = body.model_dump(exclude={"pipe_type"}, exclude_none=True)
    result = check_pipeline_compliance(body.pipe_type, params)
    return {
        "overall_compliant": result.overall_compliant,
        "rules": [asdict(r) for r in result.rules],
        "variances_needed": [asdict(r) for r in result.variances_needed],
        "warnings": result.warnings,
    }


# ─── Electrical Endpoints ─────────────────────────────────────────────────────


@router.get("/infrastructure/electrical/bbox")
async def get_electrical_bbox(
    min_lng: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lng: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    limit: int = Query(default=8000, ge=1, le=20000),
    db: AsyncSession = Depends(get_db_session),
):
    """Return electrical assets within a map viewport bbox from electrical_assets table."""
    result = await db.execute(
        text("""
            SELECT asset_id, asset_type, voltage_kv, voltage_tier, operator, name,
                   cables, source_system,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM electrical_assets
            WHERE ST_Intersects(geom, ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326))
            LIMIT :limit
        """),
        {"min_lng": min_lng, "min_lat": min_lat, "max_lng": max_lng, "max_lat": max_lat, "limit": limit},
    )
    rows = result.mappings().all()
    features = []
    for row in rows:
        tier = row["voltage_tier"] or "unknown"
        color, lwf = _voltage_tier_color(tier)

        # Map asset_type to layer_type for frontend compatibility
        layer_type = "power_line" if row["asset_type"] == "power_line" else "electrical_substation"

        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "asset_id": row["asset_id"],
                "layer_type": layer_type,
                "asset_type": row["asset_type"],
                "voltage_kv": row["voltage_kv"],
                "voltage_tier": tier,
                "voltage_color": color,
                "line_width_factor": lwf,
                "operator": row["operator"],
                "name": row["name"],
                "cables": row["cables"],
                "color": color,
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.get("/infrastructure/electrical/standards")
async def get_electrical_standards():
    """Return hardcoded Ontario electrical standards for frontend display."""
    from app.data.electrical_standards import (
        ELECTRICAL_REGULATORY_HIERARCHY,
        OBC_ELECTRICAL_FACILITIES,
        OBC_LARGE_BUILDING_ELECTRICAL,
        OESC_KEY_REQUIREMENTS,
        ESA_INSPECTION_STAGES,
        TORONTO_HYDRO_SERVICE_RATINGS,
        CEC_DEMAND_CALCULATIONS,
        POLE_TYPE_SPECS,
    )
    return {
        "regulatory_hierarchy": ELECTRICAL_REGULATORY_HIERARCHY,
        "obc_facilities": OBC_ELECTRICAL_FACILITIES,
        "obc_large_building": OBC_LARGE_BUILDING_ELECTRICAL,
        "oesc_requirements": OESC_KEY_REQUIREMENTS,
        "esa_inspections": ESA_INSPECTION_STAGES,
        "toronto_hydro_ratings": TORONTO_HYDRO_SERVICE_RATINGS,
        "cec_demand": CEC_DEMAND_CALCULATIONS,
        "voltage_tiers": VOLTAGE_TIERS,
        "pole_specs": POLE_TYPE_SPECS,
    }


@router.get("/infrastructure/electrical/nearby")
async def get_nearby_electrical(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(default=500, ge=1, le=10000),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Return electrical assets as GeoJSON within radius of a point."""
    point_wkt = f"SRID=4326;POINT({lng} {lat})"
    result = await db.execute(
        text("""
            SELECT id, asset_id, asset_type, voltage_kv, voltage_tier,
                   operator, name, cables,
                   ST_AsGeoJSON(geom)::json AS geometry,
                   ST_Distance(geom::geography, ST_GeomFromEWKT(:point)::geography) AS distance_m
            FROM electrical_assets
            WHERE ST_DWithin(geom::geography, ST_GeomFromEWKT(:point)::geography, :radius)
              AND geom IS NOT NULL
            ORDER BY distance_m
            LIMIT 200
        """),
        {"point": point_wkt, "radius": radius_m},
    )
    rows = result.mappings().all()
    features = []
    for row in rows:
        tier = row["voltage_tier"] or "unknown"
        color, lwf = _voltage_tier_color(tier)
        layer_type = "power_line" if row["asset_type"] == "power_line" else "electrical_substation"

        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "id": str(row["id"]),
                "asset_id": row["asset_id"],
                "layer_type": layer_type,
                "asset_type": row["asset_type"],
                "voltage_kv": row["voltage_kv"],
                "voltage_tier": tier,
                "voltage_color": color,
                "line_width_factor": lwf,
                "operator": row["operator"],
                "name": row["name"],
                "distance_m": round(row["distance_m"], 1) if row["distance_m"] else None,
                "color": color,
            },
        })
    return {"type": "FeatureCollection", "features": features}


@router.post("/infrastructure/compliance/electrical")
async def check_electrical(
    body: ElectricalComplianceRequest,
    user: dict = Depends(get_current_user),
):
    """Return electrical compliance context from standards data."""
    from app.data.electrical_standards import (
        OBC_ELECTRICAL_FACILITIES,
        OBC_LARGE_BUILDING_ELECTRICAL,
        OESC_KEY_REQUIREMENTS,
        TORONTO_HYDRO_SERVICE_RATINGS,
    )
    btype = body.building_type
    is_large = (body.num_floors or 1) > 3 or (body.total_area_m2 or 0) > 600
    return {
        "building_type": btype,
        "is_large_building": is_large,
        "obc_facilities": OBC_ELECTRICAL_FACILITIES,
        "obc_large_building": OBC_LARGE_BUILDING_ELECTRICAL if is_large else None,
        "oesc_requirements": OESC_KEY_REQUIREMENTS,
        "toronto_hydro_ratings": TORONTO_HYDRO_SERVICE_RATINGS,
    }


@router.post("/infrastructure/electrical/capacity-check")
async def electrical_capacity_check(
    body: CapacityCheckRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Check if nearby grid infrastructure can support a building's electrical demand."""
    point_wkt = f"SRID=4326;POINT({body.lng} {body.lat})"
    features = []

    result = await db.execute(
        text("""
            SELECT asset_id, asset_type, voltage_kv, voltage_tier,
                   operator, name,
                   ST_AsGeoJSON(geom)::json AS geometry
            FROM electrical_assets
            WHERE ST_DWithin(geom::geography, ST_GeomFromEWKT(:point)::geography, 2000)
              AND geom IS NOT NULL
            ORDER BY ST_Distance(geom::geography, ST_GeomFromEWKT(:point)::geography)
            LIMIT 200
        """),
        {"point": point_wkt},
    )
    rows = result.mappings().all()
    for row in rows:
        layer_type = "power_line" if row["asset_type"] == "power_line" else "electrical_substation"
        features.append({
            "type": "Feature",
            "geometry": row["geometry"],
            "properties": {
                "layer_type": layer_type,
                "voltage": str(row["voltage_kv"]) if row["voltage_kv"] else None,
                "operator": row["operator"],
                "name": row["name"],
            },
        })

    cap_result = run_capacity_check(
        lat=body.lat,
        lng=body.lng,
        features=features,
        building_type=body.building_type,
        building_subtype=body.building_subtype,
        requested_amps=body.requested_amps,
        num_units=body.num_units,
        total_area_m2=body.total_area_m2,
        num_floors=body.num_floors,
        has_ev_charging=body.has_ev_charging,
        has_electric_heating=body.has_electric_heating,
    )
    return cap_result
