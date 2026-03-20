/**
 * Extract a [lng, lat] centroid from a GeoJSON geometry.
 * For polygons, computes the mean of all exterior ring coordinates.
 * Returns null if geometry is unusable.
 */
export function extractCentroid(geom) {
    if (!geom?.coordinates) return null;

    if (geom.type === 'Point') {
        return geom.coordinates.length >= 2 ? geom.coordinates.slice(0, 2) : null;
    }

    let ring = null;
    if (geom.type === 'Polygon') {
        ring = geom.coordinates[0];
    } else if (geom.type === 'MultiPolygon') {
        ring = geom.coordinates[0]?.[0];
    }

    if (!ring || ring.length === 0) return null;

    let sumLng = 0, sumLat = 0;
    for (const coord of ring) {
        sumLng += coord[0];
        sumLat += coord[1];
    }
    return [sumLng / ring.length, sumLat / ring.length];
}
