// Map module — MapLibre GL JS with cadastral-style parcel rendering
// Free and open-source, no API key required

import maplibregl from 'maplibre-gl';

// Default center: Toronto
const DEFAULT_CENTER = [-79.3832, 43.6532];
const DEFAULT_ZOOM = 13;

let map = null;
let currentMarker = null;

/**
 * Initialize the MapLibre GL JS map with a cadastral/parcel appearance
 */
export function initMap() {
    map = new maplibregl.Map({
        container: 'map',
        style: {
            version: 8,
            name: 'Arterial Cadastral',
            sources: {
                'osm-tiles': {
                    type: 'raster',
                    tiles: [
                        'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
                    ],
                    tileSize: 256,
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                },
            },
            layers: [
                {
                    id: 'osm-base',
                    type: 'raster',
                    source: 'osm-tiles',
                    minzoom: 0,
                    maxzoom: 19,
                    paint: {
                        // Desaturate and darken to create the cadastral/survey map appearance
                        'raster-saturation': -0.75,
                        'raster-brightness-min': 0.08,
                        'raster-brightness-max': 0.5,
                        'raster-contrast': 0.2,
                    },
                },
            ],
            glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
        },
        center: DEFAULT_CENTER,
        zoom: DEFAULT_ZOOM,
        pitch: 0,
        bearing: 0,
        antialias: true,
        maxZoom: 19,
        minZoom: 8,
    });

    // Add navigation controls
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');

    // Add geolocation
    map.addControl(
        new maplibregl.GeolocateControl({
            positionOptions: { enableHighAccuracy: true },
            trackUserLocation: false,
        }),
        'top-right'
    );

    // On map load, add parcel layers
    map.on('load', () => {
        addParcelLayers();
    });

    return map;
}

/**
 * Add synthetic parcel boundary layers with lot numbers
 */
function addParcelLayers() {
    const center = map.getCenter();

    map.addSource('parcels', {
        type: 'geojson',
        data: generateParcels(center.lng, center.lat),
        generateId: true,
    });

    // Parcel fill — subtle base
    map.addLayer({
        id: 'parcel-fills',
        type: 'fill',
        source: 'parcels',
        paint: {
            'fill-color': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                'rgba(200, 165, 92, 0.25)',
                ['boolean', ['feature-state', 'hover'], false],
                'rgba(200, 165, 92, 0.12)',
                'rgba(200, 165, 92, 0.02)',
            ],
        },
    });

    // Parcel boundary outlines
    map.addLayer({
        id: 'parcel-outlines',
        type: 'line',
        source: 'parcels',
        paint: {
            'line-color': [
                'case',
                ['boolean', ['feature-state', 'selected'], false],
                '#c8a55c',
                '#6e5f3d',
            ],
            'line-width': [
                'interpolate', ['linear'], ['zoom'],
                12, 0.3,
                14, 0.7,
                16, 1.2,
                18, 2,
            ],
            'line-opacity': [
                'interpolate', ['linear'], ['zoom'],
                11, 0,
                13, 0.4,
                15, 0.7,
                17, 0.9,
            ],
        },
    });

    // Lot number labels
    map.addLayer({
        id: 'parcel-labels',
        type: 'symbol',
        source: 'parcels',
        layout: {
            'text-field': ['get', 'lotNumber'],
            'text-size': [
                'interpolate', ['linear'], ['zoom'],
                14, 9,
                16, 13,
                18, 17,
            ],
            'text-allow-overlap': false,
            'text-ignore-placement': false,
            'text-font': ['Open Sans Regular'],
            'text-padding': 4,
        },
        paint: {
            'text-color': '#a08c64',
            'text-halo-color': 'rgba(20, 20, 20, 0.85)',
            'text-halo-width': 1.5,
            'text-opacity': [
                'interpolate', ['linear'], ['zoom'],
                13.5, 0,
                14.5, 0.6,
                16, 0.9,
            ],
        },
        minzoom: 14,
    });

    // ── Hover interactions ──
    let hoveredId = null;

    map.on('mousemove', 'parcel-fills', (e) => {
        if (e.features.length > 0) {
            if (hoveredId !== null) {
                map.setFeatureState({ source: 'parcels', id: hoveredId }, { hover: false });
            }
            hoveredId = e.features[0].id;
            map.setFeatureState({ source: 'parcels', id: hoveredId }, { hover: true });
            map.getCanvas().style.cursor = 'pointer';
        }
    });

    map.on('mouseleave', 'parcel-fills', () => {
        if (hoveredId !== null) {
            map.setFeatureState({ source: 'parcels', id: hoveredId }, { hover: false });
            hoveredId = null;
        }
        map.getCanvas().style.cursor = '';
    });

    // ── Click to select parcel ──
    let selectedId = null;

    map.on('click', 'parcel-fills', (e) => {
        if (e.features.length > 0) {
            // Deselect previous
            if (selectedId !== null) {
                map.setFeatureState({ source: 'parcels', id: selectedId }, { selected: false });
            }

            const feature = e.features[0];
            selectedId = feature.id;
            map.setFeatureState({ source: 'parcels', id: selectedId }, { selected: true });

            // Dispatch event for other modules
            window.dispatchEvent(
                new CustomEvent('parcel-selected', {
                    detail: {
                        id: feature.properties.id,
                        address: feature.properties.address,
                        lotNumber: feature.properties.lotNumber,
                        zoning: feature.properties.zoning,
                        lotArea: feature.properties.lotArea,
                        frontage: feature.properties.frontage,
                        coordinates: e.lngLat,
                    },
                })
            );
        }
    });

    // ── Regenerate parcels on map move (when zoomed in) ──
    let moveTimeout = null;
    map.on('moveend', () => {
        clearTimeout(moveTimeout);
        moveTimeout = setTimeout(() => {
            if (map.getZoom() >= 13) {
                const c = map.getCenter();
                const src = map.getSource('parcels');
                if (src) {
                    src.setData(generateParcels(c.lng, c.lat));
                }
            }
        }, 200);
    });
}

/**
 * Generate realistic synthetic parcel data with lot numbers
 * Mimics a Toronto-style residential/commercial grid
 */
function generateParcels(centerLng, centerLat) {
    const features = [];
    const GRID = 20;
    const BASE_WIDTH = 0.00035;  // ~27m lot width
    const BASE_DEPTH = 0.00055;  // ~42m lot depth
    const STREET_GAP = 0.00012;

    const startLng = centerLng - (GRID / 2) * BASE_WIDTH - 2 * STREET_GAP;
    const startLat = centerLat - (GRID / 2) * BASE_DEPTH - 2 * STREET_GAP;

    const zonings = ['R', 'RD', 'RS', 'RT', 'RM', 'RA', 'CR', 'CRE'];
    const streets = ['Poplar Ave', 'Oak St', 'Maple Rd', 'Elm Dr', 'Cedar Ln', 'Birch Blvd', 'Pine Way', 'Spruce St'];

    // Use a seed based on center for stable lot numbers
    const seed = Math.abs(Math.floor(centerLng * 1000) + Math.floor(centerLat * 1000));

    let id = 0;
    for (let row = 0; row < GRID; row++) {
        const blockRow = Math.floor(row / 5);
        const rowGap = blockRow * STREET_GAP;

        for (let col = 0; col < GRID; col++) {
            const blockCol = Math.floor(col / 5);
            const colGap = blockCol * STREET_GAP;

            // Skip cells that are "streets" (every 5th row/col boundary)
            if (row % 5 === 4 || col % 5 === 4) continue;

            // Lot size variation
            const wVar = 0.88 + pseudoRandom(seed + id * 3) * 0.24;
            const dVar = 0.88 + pseudoRandom(seed + id * 7) * 0.24;

            const lng = startLng + col * BASE_WIDTH + colGap;
            const lat = startLat + row * BASE_DEPTH + rowGap;
            const w = BASE_WIDTH * wVar;
            const d = BASE_DEPTH * dVar;

            const lotNum = ((seed + id * 17) % 900 + 10).toString();
            const streetIdx = (blockRow * 4 + blockCol) % streets.length;
            const houseNum = 2 + (col % 5) * 4 + Math.floor(pseudoRandom(seed + id) * 4);
            const address = `${houseNum} ${streets[streetIdx]}`;

            const zoningIdx = Math.floor(pseudoRandom(seed + id * 11) * zonings.length);
            const cosLat = Math.cos(lat * Math.PI / 180);
            const lotAreaM2 = Math.floor(w * 111320 * cosLat * d * 110540);

            features.push({
                type: 'Feature',
                id: id,
                properties: {
                    id: `parcel-${seed}-${id}`,
                    lotNumber: lotNum,
                    address: address,
                    zoning: zonings[zoningIdx],
                    lotArea: lotAreaM2,
                    frontage: (w * 111320 * cosLat).toFixed(1),
                },
                geometry: {
                    type: 'Polygon',
                    coordinates: [[
                        [lng, lat],
                        [lng + w, lat],
                        [lng + w, lat + d],
                        [lng, lat + d],
                        [lng, lat],
                    ]],
                },
            });
            id++;
        }
    }

    return { type: 'FeatureCollection', features };
}

/**
 * Deterministic pseudo-random based on seed for stable parcel generation
 */
function pseudoRandom(seed) {
    const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
    return x - Math.floor(x);
}

/**
 * Fly the map to a specific location with smooth animation
 */
export function flyTo(lng, lat, zoom = 16) {
    if (!map) return;
    map.flyTo({
        center: [lng, lat],
        zoom: zoom,
        duration: 2200,
        essential: true,
        curve: 1.42,
    });
}

/**
 * Place a marker at coordinates
 */
export function setMarker(lng, lat) {
    if (!map) return;
    if (currentMarker) currentMarker.remove();

    const el = document.createElement('div');
    el.style.cssText = 'width:36px;height:36px;cursor:pointer;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.5));';
    el.innerHTML = `<svg viewBox="0 0 24 24" fill="#c8a55c" stroke="#1a1a1a" stroke-width="1.5" width="36" height="36"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3" fill="#1a1a1a"/></svg>`;

    currentMarker = new maplibregl.Marker({ element: el, anchor: 'bottom' })
        .setLngLat([lng, lat])
        .addTo(map);
}

export function getMap() {
    return map;
}
