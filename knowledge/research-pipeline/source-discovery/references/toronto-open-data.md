---
title: "Toronto Open Data — API & Endpoint Reference"
category: source-discovery
relevance: "Load when querying Toronto-specific CKAN datasets, building spatial queries, or checking data freshness for Toronto Open Data."
key_topics: "CKAN API, zoning GeoJSON, address points, heritage register, development applications, building permits, point-in-polygon, geocoding, DQS"
---

# Toronto Open Data — API & Endpoint Reference

Toronto uses the CKAN open data platform. All datasets are queryable via the CKAN API or direct download.

## Base API Pattern

```
GET https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show
  ?id={package_name_or_id}
```

To get the download URL for a specific resource within a package:
```
GET https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show
  ?id=zoning-by-law

# Response: .result.resources[] — each resource has a .url field
```

---

## Key Datasets

### Zoning By-law
- **Package ID**: `zoning-by-law`
- **Direct API**: `https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=zoning-by-law`
- **Format**: SHP, GeoJSON, FileGDB
- **Key fields**: `ZBL_ZONE` (zone code), `HT` (height m), `LOT_COV` (lot coverage %), `ZONE_DESC`
- **Spatial query**: Use GeoJSON endpoint with bounding box or point-in-polygon to get zone for a coordinate

### Address Points (Municipal 1:25K)
- **Package ID**: `address-points-municipal-25k`
- **Format**: GeoJSON, CSV
- **Key fields**: `LFNAME` (street name), `MUN_UNIT` (unit), `LNG`, `LAT`, `WARD_NAME`
- **Use**: First step — resolve input address to lat/lon coordinates

### Official Plan Land Use Designations
- **Package ID**: `official-plan-land-use-designations`
- **Format**: SHP, GeoJSON
- **Key fields**: `LAND_USE_D` (designation label)
- **Use**: Point-in-polygon to get OP designation for a coordinate

### Heritage Register
- **Package ID**: `heritage-register`
- **Format**: CSV, JSON
- **Key fields**: `ADDRESS`, `STATUS` (Listed/Designated), `HERITAGE_TYPE`, `HCD` (heritage conservation district flag)
- **Use**: String match on address or spatial join

### Development Applications
- **Package ID**: `development-applications`
- **Format**: JSON, CSV
- **Key fields**: `ADDRESS`, `APPLICATION_TYPE`, `STATUS`, `SUBMITTED_DATE`, `DECISION_DATE`, `WARD`
- **Use**: Filter by address to surface active or recent ZBAs, OPAs, site plan applications

### Building Permits — Active
- **Package ID**: `building-permits-active-permits`
- **Format**: JSON, CSV
- **Key fields**: `ADDRESS`, `PERMIT_TYPE`, `DESCRIPTION_OF_WORK`, `UNITS_ADDED`, `PROPOSED_GFA`, `STATUS`

### Building Permits — Cleared (Historical)
- **Package ID**: `building-permits-cleared-permits`
- **Format**: JSON, CSV
- **Notes**: Historical completed permits. Combine with active permits for full picture.

---

## Spatial Query Pattern (Point-in-Polygon)

To find what zone a coordinate falls in:

```python
# 1. Download zoning GeoJSON (cache locally — large file)
# 2. Use shapely or turf.js point-in-polygon
import geopandas as gpd
from shapely.geometry import Point

zoning = gpd.read_file("toronto_zoning.geojson")
point = Point(-79.3832, 43.6532)  # lng, lat
result = zoning[zoning.geometry.contains(point)]
zone_code = result.iloc[0]["ZBL_ZONE"]  # e.g., "RD"
```

For lightweight server queries, use the ArcGIS Feature Service identify endpoint instead of downloading the full dataset:
```
GET https://gis.toronto.ca/arcgis/rest/services/cot_geospatial7/MapServer/{layerId}/query
  ?geometry={lon},{lat}
  &geometryType=esriGeometryPoint
  &spatialRel=esriSpatialRelIntersects
  &outFields=*
  &f=json
```

---

## Address Geocoding

Toronto does not have a public geocoding API. Options:
1. **Self-geocode**: Match against the Address Points dataset (exact match on street number + name)
2. **Nominatim (OpenStreetMap)**: Free, reasonable accuracy for Toronto addresses
   - `https://nominatim.openstreetmap.org/search?q={address}&format=json&limit=1`
3. **Google Geocoding API**: Most accurate but paid past free tier

Recommended pipeline: Nominatim first → validate against Toronto Address Points dataset → flag if no match.

---

## Data Freshness Check

All Toronto Open Data packages include a `last_modified` field in the CKAN package metadata:
```
GET https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=zoning-by-law
# Check: .result.metadata_modified
```

⚠️ If `last_modified` is >90 days ago for the zoning dataset, flag in the source bundle that the zoning data may not reflect recent Council amendments.

---

## Data Quality Score (DQS)

Toronto Open Data rates datasets using a DQS across 5 factors: Freshness (35%), Metadata (35%), Accessibility (15%), Completeness (10%), Usability (5%).

**Pipeline rule**: Prefer datasets with Gold status (DQS >80%). Query DQS from the CKAN metadata when evaluating source reliability. Datasets with DQS <60% should be marked as `confidence: "low"` in the source bundle.

```
GET https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id={package_id}
# Check: .result.extras[] for quality_score field if present
```
