"""Generic ArcGIS REST FeatureServer client with pagination, metadata, and retry."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Iterator

import httpx
import structlog

logger = structlog.get_logger()

ARCGIS_BASE = "https://gis.toronto.ca/arcgis/rest/services"
DEFAULT_PAGE_SIZE = 2000
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2.0
REQUEST_TIMEOUT = 120


@dataclass
class LayerMetadata:
    """Metadata about an ArcGIS FeatureServer layer."""
    name: str
    max_record_count: int
    fields: list[dict[str, Any]]
    geometry_type: str
    crs_wkid: int
    object_id_field: str = "OBJECTID"


@dataclass
class FetchResult:
    """Result from fetching a single page of features."""
    features: list[dict[str, Any]]
    exceeded_transfer_limit: bool = False


def _build_layer_url(service_url: str, layer_id: int) -> str:
    """Build full layer URL from service path and layer ID."""
    base = service_url.rstrip("/")
    if not base.startswith("http"):
        base = f"{ARCGIS_BASE}/{base}"
    # Ensure FeatureServer is in the path
    if "/FeatureServer" not in base and "/MapServer" not in base:
        base = f"{base}/FeatureServer"
    return f"{base}/{layer_id}"


def _request_with_retry(
    url: str,
    params: dict[str, Any],
    *,
    max_retries: int = MAX_RETRIES,
    timeout: int = REQUEST_TIMEOUT,
) -> dict[str, Any]:
    """Make a GET request with exponential backoff retry on 5xx/timeout."""
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            resp = httpx.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                err = data["error"]
                raise ValueError(f"ArcGIS error {err.get('code')}: {err.get('message')}")
            return data
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError, ValueError) as exc:
            last_exc = exc
            if attempt < max_retries:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning(
                    "arcgis.retry",
                    url=url,
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(exc),
                )
                time.sleep(wait)
    raise last_exc  # type: ignore[misc]


def get_layer_metadata(service_url: str, layer_id: int) -> LayerMetadata:
    """Fetch metadata for an ArcGIS FeatureServer layer."""
    layer_url = _build_layer_url(service_url, layer_id)
    data = _request_with_retry(layer_url, {"f": "json"})
    return LayerMetadata(
        name=data.get("name", ""),
        max_record_count=data.get("maxRecordCount", DEFAULT_PAGE_SIZE),
        fields=data.get("fields", []),
        geometry_type=data.get("geometryType", ""),
        crs_wkid=data.get("extent", {}).get("spatialReference", {}).get("wkid", 4326),
        object_id_field=data.get("objectIdField", "OBJECTID"),
    )


def fetch_page(
    service_url: str,
    layer_id: int,
    *,
    offset: int = 0,
    page_size: int = DEFAULT_PAGE_SIZE,
    where: str = "1=1",
    out_fields: str = "*",
) -> FetchResult:
    """Fetch one page of GeoJSON features from an ArcGIS FeatureServer layer."""
    layer_url = _build_layer_url(service_url, layer_id)
    query_url = f"{layer_url}/query"
    params = {
        "where": where,
        "outFields": out_fields,
        "outSR": "4326",
        "f": "geojson",
        "resultOffset": offset,
        "resultRecordCount": page_size,
        "returnGeometry": "true",
    }
    data = _request_with_retry(query_url, params)
    features = data.get("features", [])
    exceeded = data.get("exceededTransferLimit", False)
    return FetchResult(features=features, exceeded_transfer_limit=exceeded)


def fetch_object_ids(
    service_url: str,
    layer_id: int,
    *,
    where: str = "1=1",
) -> list[int]:
    """Fetch all object IDs for a layer (used for reliable pagination)."""
    layer_url = _build_layer_url(service_url, layer_id)
    query_url = f"{layer_url}/query"
    params = {
        "where": where,
        "returnIdsOnly": "true",
        "f": "json",
    }
    data = _request_with_retry(query_url, params)
    return sorted(data.get("objectIds", []))


def iter_all_features(
    service_url: str,
    layer_id: int,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    where: str = "1=1",
    out_fields: str = "*",
) -> Iterator[dict[str, Any]]:
    """Paginated iterator over all features in an ArcGIS FeatureServer layer.

    Uses objectIds-based pagination for reliability (offset-based pagination
    can miss or duplicate records on large layers).
    """
    meta = get_layer_metadata(service_url, layer_id)
    effective_page_size = min(page_size, meta.max_record_count)
    oid_field = meta.object_id_field

    all_ids = fetch_object_ids(service_url, layer_id, where=where)
    total = len(all_ids)
    logger.info("arcgis.iter_start", layer=meta.name, total_features=total)

    layer_url = _build_layer_url(service_url, layer_id)
    query_url = f"{layer_url}/query"

    for batch_start in range(0, total, effective_page_size):
        batch_ids = all_ids[batch_start : batch_start + effective_page_size]
        oid_min = batch_ids[0]
        oid_max = batch_ids[-1]
        oid_where = f"{oid_field} >= {oid_min} AND {oid_field} <= {oid_max}"

        params = {
            "where": oid_where,
            "outFields": out_fields,
            "outSR": "4326",
            "f": "geojson",
            "returnGeometry": "true",
        }
        data = _request_with_retry(query_url, params)
        features = data.get("features", [])
        yield from features

        fetched_so_far = min(batch_start + effective_page_size, total)
        if fetched_so_far % 10000 < effective_page_size:
            logger.info("arcgis.progress", layer=meta.name, fetched=fetched_so_far, total=total)
