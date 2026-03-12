"""Electrical infrastructure ingestion service.

Ingests power lines and substations from OpenStreetMap Overpass API into the
`electrical_assets` table. Pole data (305K street lights / traffic signals)
is no longer ingested — it's utility-operations data, not feasibility data.
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.data.electrical_standards import VOLTAGE_TIERS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TORONTO_BBOX = (43.58, -79.64, 43.86, -79.12)  # (south, west, north, east)
OVERPASS_API = "https://overpass-api.de/api/interpreter"

OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:120];
(
  way["power"="line"]({s},{w},{n},{e});
  way["power"="cable"]({s},{w},{n},{e});
  node["power"="substation"]({s},{w},{n},{e});
  way["power"="substation"]({s},{w},{n},{e});
  node["power"="transformer"]({s},{w},{n},{e});
);
out body;
>;
out skel qt;
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_int(val: Any) -> int | None:
    try:
        return int(float(val)) if val is not None else None
    except (ValueError, TypeError):
        return None


def _classify_voltage_tier(voltage_raw: str | None) -> tuple[float, str]:
    """Parse raw voltage string -> (voltage_kv, tier_key)."""
    if not voltage_raw:
        return 0.0, "unknown"

    s = str(voltage_raw).strip().lower().replace(",", "").replace("kv", "").replace("v", "").strip()
    try:
        val = float(s)
    except ValueError:
        m = re.search(r"[\d.]+", s)
        val = float(m.group()) if m else 0.0
    if val > 1000:
        val /= 1000
    kv = val

    for key, tier in VOLTAGE_TIERS.items():
        if key == "unknown":
            continue
        if tier["min_kv"] <= kv <= tier["max_kv"]:
            return kv, key

    return kv, "unknown"


# ---------------------------------------------------------------------------
# Overpass query
# ---------------------------------------------------------------------------


def _query_overpass() -> dict:
    s, w, n, e = TORONTO_BBOX
    query = OVERPASS_QUERY_TEMPLATE.format(s=s, w=w, n=n, e=e)
    resp = httpx.post(OVERPASS_API, data={"data": query}, timeout=180)
    resp.raise_for_status()
    return resp.json()


def _build_node_index(elements: list[dict]) -> dict[int, tuple[float, float]]:
    index = {}
    for el in elements:
        if el.get("type") == "node":
            index[el["id"]] = (el.get("lon", 0), el.get("lat", 0))
    return index


def _way_to_linestring_ewkt(way: dict, node_index: dict) -> str | None:
    node_ids = way.get("nodes", [])
    coords = [node_index[nid] for nid in node_ids if nid in node_index]
    if len(coords) < 2:
        return None
    pts = ", ".join(f"{lon} {lat}" for lon, lat in coords)
    return f"SRID=4326;LINESTRING({pts})"


def _node_to_point_ewkt(node: dict) -> str | None:
    lon = node.get("lon")
    lat = node.get("lat")
    if lon is None or lat is None:
        return None
    return f"SRID=4326;POINT({lon} {lat})"


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------


def ingest_power_lines_osm(db: Session) -> dict:
    """Query Overpass for Toronto power lines and substations.

    Writes to `electrical_assets` table. Returns summary dict.
    """
    from app.models.infrastructure import ElectricalAsset

    logger.info("Querying Overpass API for Toronto power infrastructure...")
    data = _query_overpass()
    elements = data.get("elements", [])

    node_index = _build_node_index(elements)
    inserted = 0
    errors = 0

    for el in elements:
        el_type = el.get("type")
        tags = el.get("tags", {})
        power_tag = tags.get("power")

        if not power_tag:
            continue

        try:
            voltage_raw = tags.get("voltage")
            voltage_kv, voltage_tier = _classify_voltage_tier(voltage_raw)
            operator = tags.get("operator")
            name = tags.get("name")
            cables = _safe_int(tags.get("cables"))

            if power_tag in ("line", "cable") and el_type == "way":
                ewkt = _way_to_linestring_ewkt(el, node_index)
                if not ewkt:
                    continue

                asset = ElectricalAsset(
                    id=uuid.uuid4(),
                    asset_id=f"osm_way_{el['id']}",
                    asset_type="power_line",
                    voltage_kv=voltage_kv if voltage_kv else None,
                    voltage_tier=voltage_tier,
                    operator=operator,
                    name=name,
                    cables=cables,
                    source_system="osm",
                    geom=ewkt,
                    attributes_json={
                        "osm_id": el["id"],
                        "power_type": power_tag,
                        "voltage_raw": voltage_raw,
                    },
                )
                db.add(asset)
                inserted += 1

            elif power_tag in ("substation", "transformer"):
                if el_type == "node":
                    ewkt = _node_to_point_ewkt(el)
                elif el_type == "way":
                    node_ids = el.get("nodes", [])
                    coords = [node_index[nid] for nid in node_ids if nid in node_index]
                    if not coords:
                        continue
                    avg_lon = sum(c[0] for c in coords) / len(coords)
                    avg_lat = sum(c[1] for c in coords) / len(coords)
                    ewkt = f"SRID=4326;POINT({avg_lon} {avg_lat})"
                else:
                    continue

                if not ewkt:
                    continue

                asset = ElectricalAsset(
                    id=uuid.uuid4(),
                    asset_id=f"osm_{el_type}_{el['id']}",
                    asset_type="substation",
                    voltage_kv=voltage_kv if voltage_kv else None,
                    voltage_tier=voltage_tier,
                    operator=operator,
                    name=name,
                    cables=None,
                    source_system="osm",
                    geom=ewkt,
                    attributes_json={
                        "osm_id": el["id"],
                        "power_type": power_tag,
                        "voltage_raw": voltage_raw,
                        "substation_type": tags.get("substation"),
                    },
                )
                db.add(asset)
                inserted += 1

            if inserted % 500 == 0 and inserted > 0:
                db.flush()

        except Exception as exc:
            errors += 1
            logger.warning("Error inserting OSM element %s: %s", el.get("id"), exc)

    db.commit()
    logger.info("OSM power ingestion complete: %d inserted, %d errors", inserted, errors)
    return {"status": "ok", "inserted": inserted, "errors": errors}


# ---------------------------------------------------------------------------
# Seed entry point
# ---------------------------------------------------------------------------


def seed_all_electrical_layers(db: Session) -> dict:
    """Ingest all electrical data sources (OSM power lines + substations)."""
    results = {}
    try:
        results["osm_power"] = ingest_power_lines_osm(db)
    except Exception as exc:
        logger.error("OSM power ingestion failed: %s", exc)
        results["osm_power"] = {"status": "error", "message": str(exc)}
    return results
