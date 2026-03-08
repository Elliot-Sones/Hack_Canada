"""Infrastructure endpoints — nearby assets and compliance checks.

Returns GeoJSON FeatureCollections so the map can render infrastructure layers directly.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session

# ─── File-based watermain cache ───────────────────────────────────────────────
_WATERMAIN_CACHE: list | None = None
_DATA_DIR = pathlib.Path(__file__).parent.parent.parent / "water-system-data"


def _load_watermains() -> list:
    global _WATERMAIN_CACHE
    if _WATERMAIN_CACHE is not None:
        return _WATERMAIN_CACHE
    path = _DATA_DIR / "Watermain Distribution 4326.geojson"
    with open(path, encoding="utf-8") as f:
        fc = json.load(f)
    _WATERMAIN_CACHE = fc.get("features", [])
    return _WATERMAIN_CACHE


def _geom_intersects_bbox(geom: dict, min_lng: float, min_lat: float, max_lng: float, max_lat: float) -> bool:
    """Check if a MultiLineString / LineString geometry intersects the bbox."""
    coords_list = geom.get("coordinates", [])
    if geom["type"] == "MultiLineString":
        for line in coords_list:
            for pt in line:
                if min_lng <= pt[0] <= max_lng and min_lat <= pt[1] <= max_lat:
                    return True
    elif geom["type"] == "LineString":
        for pt in coords_list:
            if min_lng <= pt[0] <= max_lng and min_lat <= pt[1] <= max_lat:
                return True
    return False
from app.schemas.infrastructure import PipelineComplianceRequest
from app.services.infrastructure_compliance import check_pipeline_compliance

router = APIRouter()

# Pipe-type → hex color for map rendering
PIPE_COLORS = {
    "water_main": "#2277bb",
    "sanitary_sewer": "#886644",
    "storm_sewer": "#44aa66",
    "gas_line": "#ddaa22",
}


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
                   install_year, depth_m, slope_pct, attributes_json,
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
                "distance_m": round(row["distance_m"], 1) if row["distance_m"] else None,
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



@router.get("/infrastructure/watermains/bbox")
async def get_watermains_bbox(
    min_lng: float = Query(..., ge=-180, le=180),
    min_lat: float = Query(..., ge=-90, le=90),
    max_lng: float = Query(..., ge=-180, le=180),
    max_lat: float = Query(..., ge=-90, le=90),
    limit: int = Query(default=3000, ge=1, le=10000),
):
    """Return Toronto watermain segments within a map viewport bbox.

    Reads directly from the committed GeoJSON dataset — no DB required.
    Properties are normalised to match the map's pipeline layer schema.
    """
    features_raw = _load_watermains()
    out = []
    for feat in features_raw:
        if len(out) >= limit:
            break
        geom = feat.get("geometry")
        if not geom:
            continue
        if not _geom_intersects_bbox(geom, min_lng, min_lat, max_lng, max_lat):
            continue
        p = feat.get("properties", {})
        diameter = p.get("Watermain Diameter")
        material = p.get("Watermain Material") or "UNK"
        year_raw = p.get("Watermain Construction Year")
        install_year = int(year_raw) if year_raw and str(year_raw).isdigit() else None
        out.append({
            "type": "Feature",
            "geometry": geom,
            "properties": {
                "asset_id": p.get("Watermain Asset Identification"),
                "pipe_type": "water_main",
                "material": material,
                "diameter_mm": int(diameter) if diameter else None,
                "install_year": install_year,
                "location": p.get("Watermain Location Description"),
                "length_m": p.get("Watermain Measured Length"),
                "color": "#2277bb",
            },
        })
    return {"type": "FeatureCollection", "features": out}
