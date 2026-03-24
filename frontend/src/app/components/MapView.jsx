import { useEffect, useRef, useImperativeHandle, forwardRef, useState, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../styles/ModelViewer.css';
import { searchParcelsBbox } from '../api.js';

const DEFAULT_CENTER = [-79.3832, 43.6532];
const DEFAULT_ZOOM = 13;

const EMPTY_FC = { type: 'FeatureCollection', features: [] };

const MapView = forwardRef(function MapView({ isParcelResolved, onModelOpen, isPanelOpen, isSidebarCollapsed, isChatExpanded, chatPanelHeight = 49, isModelOpen, infraOverlayLayers = new Set(), onParcelClick }, ref) {
    const containerRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markerRef = useRef(null);
    const popupRef = useRef(null);
    const hoverPopupRef = useRef(null);
    const [mapLoaded, setMapLoaded] = useState(false);
    const onParcelClickRef = useRef(onParcelClick);
    useEffect(() => { onParcelClickRef.current = onParcelClick; }, [onParcelClick]);
    const hoveredParcelIdRef = useRef(null);
    const selectedParcelIdsRef = useRef([]);
    const bboxAbortRef = useRef(null);
    const bboxDebounceRef = useRef(null);

    // Store geojson safely if set before map loads
    const pendingParcelRef = useRef(null);
    const pendingMassingRef = useRef(null);

    useImperativeHandle(ref, () => ({
        getMap() {
            return mapInstanceRef.current;
        },
        flyTo(lng, lat, zoom = 16) {
            if (!mapInstanceRef.current) return;
            mapInstanceRef.current.flyTo({
                center: [lng, lat],
                zoom,
                duration: 2200,
                essential: true,
                curve: 1.42,
            });
        },
        setMarker(lng, lat) {
            const map = mapInstanceRef.current;
            if (!map) return;
            if (markerRef.current) markerRef.current.remove();

            const el = document.createElement('div');
            el.style.cssText = 'width:36px;height:36px;cursor:pointer;filter:drop-shadow(0 2px 6px rgba(0,0,0,0.5));';
            el.innerHTML = `<svg viewBox="0 0 24 24" fill="#c8a55c" stroke="#1a1a1a" stroke-width="1.5" width="36" height="36"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3" fill="#1a1a1a"/></svg>`;

            markerRef.current = new maplibregl.Marker({ element: el, anchor: 'bottom' })
                .setLngLat([lng, lat])
                .addTo(map);
        },
        setParcel(geojson) {
            if (!mapLoaded) {
                pendingParcelRef.current = geojson;
                return;
            }
            const map = mapInstanceRef.current;
            if (!map) return;
            if (map.getSource('parcel')) {
                map.getSource('parcel').setData(geojson || EMPTY_FC);
            }

            // Re-show buildings if parcel clears
            if (!geojson && map.getLayer('osm-buildings-3d')) {
                map.setFilter('osm-buildings-3d', null);
            }
        },
        setProposedMassing(geojson, height_m) {
            if (!mapLoaded) {
                pendingMassingRef.current = { geojson, height_m };
                return;
            }
            const map = mapInstanceRef.current;
            if (!map) return;

            if (map.getSource('proposed-massing')) {
                map.getSource('proposed-massing').setData(geojson || EMPTY_FC);
            }

            if (height_m && geojson) {
                map.setPaintProperty('proposed-massing-extrusion', 'fill-extrusion-height', height_m);
                map.flyTo({
                    pitch: 60,
                    bearing: 20,
                    duration: 3000,
                    essential: true
                });
            } else if (geojson === null) {
                if (map.getSource('proposed-massing')) {
                    const data = map.getSource('proposed-massing')._data;
                    if (data?.features?.length > 0) {
                        map.flyTo({
                            pitch: 0,
                            bearing: 0,
                            duration: 2000,
                            essential: true
                        });
                    }
                }
            }
        },
        /** Load water main GeoJSON onto the map */
        setWatermains(geojson) {
            const map = mapInstanceRef.current;
            if (!map || !mapLoaded) return;
            const fc = geojson || EMPTY_FC;
            if (map.getSource('watermains')) {
                map.getSource('watermains').setData(fc);
            }
        },
        /** Load sewer GeoJSON onto the map */
        setSewers(geojson) {
            const map = mapInstanceRef.current;
            if (!map || !mapLoaded) return;
            if (map.getSource('sewers')) {
                map.getSource('sewers').setData(geojson || EMPTY_FC);
            }
        },
        /** Load electrical GeoJSON onto the map */
        setElectrical(geojson) {
            const map = mapInstanceRef.current;
            if (!map || !mapLoaded) return;
            if (map.getSource('electrical')) {
                map.getSource('electrical').setData(geojson || EMPTY_FC);
            }
        },
        /** Sync selected parcel highlights on the bbox layer */
        setSelectedParcelIds(ids) {
            const map = mapInstanceRef.current;
            if (!map || !mapLoaded || !map.getSource('parcels-bbox')) return;
            // Clear previous selections
            for (const prevId of selectedParcelIdsRef.current) {
                try { map.setFeatureState({ source: 'parcels-bbox', id: prevId }, { selected: false }); } catch {}
            }
            // Apply new selections
            for (const id of ids) {
                try { map.setFeatureState({ source: 'parcels-bbox', id }, { selected: true }); } catch {}
            }
            selectedParcelIdsRef.current = ids;
        },
    }));

    // Toggle infrastructure overlay layers based on infraOverlayLayers set
    useEffect(() => {
        const map = mapInstanceRef.current;
        if (!map || !mapLoaded) return;

        const pipelineLayers = ['watermains-line', 'watermains-line-casing', 'watermains-label'];
        const sewerLayers = ['sewers-line', 'sewers-line-casing'];
        const electricalLayers = ['electrical-line'];

        const showPipes = infraOverlayLayers?.has('watermains');
        const showSewers = infraOverlayLayers?.has('sewers');
        const showElectrical = infraOverlayLayers?.has('electrical');

        for (const id of pipelineLayers) {
            if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', showPipes ? 'visible' : 'none');
        }
        for (const id of sewerLayers) {
            if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', showSewers ? 'visible' : 'none');
        }
        for (const id of electricalLayers) {
            if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', showElectrical ? 'visible' : 'none');
        }
    }, [infraOverlayLayers, mapLoaded]);

    useEffect(() => {
        if (mapInstanceRef.current) return;

        const map = new maplibregl.Map({
            container: containerRef.current,
            style: 'https://tiles.openfreemap.org/styles/liberty',
            center: DEFAULT_CENTER,
            zoom: DEFAULT_ZOOM,
            pitch: 0,
            bearing: 0,
            antialias: true,
            maxZoom: 19,
            minZoom: 8,
        });

        mapInstanceRef.current = map;

        map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
        map.addControl(
            new maplibregl.GeolocateControl({
                positionOptions: { enableHighAccuracy: true },
                trackUserLocation: false,
            }),
            'top-right'
        );

        map.on('style.load', () => {
            setMapLoaded(true);

            // Hide POI / shop name labels, show house numbers instead
            const style = map.getStyle();
            if (style?.layers) {
                for (const layer of style.layers) {
                    if (layer.id.includes('poi') || layer.id.includes('shop') || layer.id.includes('amenity')) {
                        map.setLayoutProperty(layer.id, 'visibility', 'none');
                    }
                    if (layer.id.includes('housenumber') || layer.id.includes('house-number') || layer.id.includes('address')) {
                        map.setLayoutProperty(layer.id, 'visibility', 'visible');
                        map.setPaintProperty(layer.id, 'text-color', '#555555');
                        map.setPaintProperty(layer.id, 'text-opacity', 1);
                    }
                }
            }

            // Add housenumber layer if none exists in the style
            if (map.getSource('openmaptiles') && !style?.layers?.some(l => l.id.includes('housenumber'))) {
                map.addLayer({
                    id: 'housenumber-labels',
                    type: 'symbol',
                    source: 'openmaptiles',
                    'source-layer': 'housenumber',
                    minzoom: 16,
                    layout: {
                        'text-field': '{housenumber}',
                        'text-size': 11,
                        'text-anchor': 'center',
                        'text-allow-overlap': false,
                    },
                    paint: {
                        'text-color': '#444444',
                        'text-halo-color': '#ffffff',
                        'text-halo-width': 1.5,
                    }
                });
            }

            // ─── Building Layers ───────────────────────────
            map.addLayer({
                'id': 'osm-buildings-3d',
                'source': 'openmaptiles',
                'source-layer': 'building',
                'type': 'fill-extrusion',
                'minzoom': 14,
                'paint': {
                    'fill-extrusion-color': '#e0e0e0',
                    'fill-extrusion-height': ['get', 'render_height'],
                    'fill-extrusion-base': ['get', 'render_min_height'],
                    'fill-extrusion-opacity': [
                        'interpolate', ['linear'], ['zoom'],
                        14, 0.6,
                        15, 0.35,
                        17, 0.25,
                    ],
                }
            });

            map.addSource('parcel', {
                type: 'geojson',
                data: pendingParcelRef.current || EMPTY_FC
            });

            map.addLayer({
                id: 'parcel-fill',
                type: 'fill',
                source: 'parcel',
                paint: {
                    'fill-color': '#c8a55c',
                    'fill-opacity': 0.2
                }
            });

            map.addLayer({
                id: 'parcel-line',
                type: 'line',
                source: 'parcel',
                paint: {
                    'line-color': '#c8a55c',
                    'line-width': 2
                }
            });

            const pendingM = pendingMassingRef.current;
            map.addSource('proposed-massing', {
                type: 'geojson',
                data: pendingM?.geojson || EMPTY_FC
            });

            map.addLayer({
                id: 'proposed-massing-extrusion',
                type: 'fill-extrusion',
                source: 'proposed-massing',
                paint: {
                    'fill-extrusion-color': '#c8a55c',
                    'fill-extrusion-height': pendingM?.height_m || 10,
                    'fill-extrusion-base': 0,
                    'fill-extrusion-opacity': 0.85
                }
            });

            // ─── Bbox Parcel Layer (click-to-select) ────────
            map.addSource('parcels-bbox', {
                type: 'geojson',
                data: EMPTY_FC,
                promoteId: 'id',
            });

            // Parcel bbox fill layer (rendered below 3D buildings — used for queryRenderedFeatures)
            map.addLayer({
                id: 'parcels-bbox-fill',
                type: 'fill',
                source: 'parcels-bbox',
                minzoom: 15,
                paint: {
                    'fill-color': [
                        'case',
                        ['boolean', ['feature-state', 'selected'], false], '#c8a55c',
                        ['boolean', ['feature-state', 'hover'], false], '#c8a55c',
                        'rgba(200,165,92,0.06)',
                    ],
                    'fill-opacity': [
                        'case',
                        ['boolean', ['feature-state', 'selected'], false], 0.35,
                        ['boolean', ['feature-state', 'hover'], false], 0.25,
                        1,
                    ],
                },
            });

            // Parcel bbox outlines — add BEFORE 3D buildings so they peek through gaps
            map.addLayer({
                id: 'parcels-bbox-line',
                type: 'line',
                source: 'parcels-bbox',
                minzoom: 15,
                paint: {
                    'line-color': [
                        'case',
                        ['boolean', ['feature-state', 'selected'], false], '#c8a55c',
                        ['boolean', ['feature-state', 'hover'], false], '#c8a55c',
                        'rgba(200,165,92,0.5)',
                    ],
                    'line-width': [
                        'case',
                        ['boolean', ['feature-state', 'selected'], false], 2.5,
                        ['boolean', ['feature-state', 'hover'], false], 2,
                        1.2,
                    ],
                },
            });

            // Map-level mousemove — uses queryRenderedFeatures so it works through 3D buildings
            map.on('mousemove', (e) => {
                if (map.getZoom() < 15) return;
                const features = map.queryRenderedFeatures(e.point, { layers: ['parcels-bbox-fill'] });
                if (!features.length) {
                    // Clear hover when not on a parcel
                    if (hoveredParcelIdRef.current) {
                        try { map.setFeatureState({ source: 'parcels-bbox', id: hoveredParcelIdRef.current }, { hover: false }); } catch {}
                        hoveredParcelIdRef.current = null;
                    }
                    map.getCanvas().style.cursor = '';
                    if (hoverPopupRef.current) { hoverPopupRef.current.remove(); hoverPopupRef.current = null; }
                    return;
                }
                const feat = features[0];
                const fid = feat.properties.id || feat.id;

                // Clear previous hover
                if (hoveredParcelIdRef.current && hoveredParcelIdRef.current !== fid) {
                    try { map.setFeatureState({ source: 'parcels-bbox', id: hoveredParcelIdRef.current }, { hover: false }); } catch {}
                }
                hoveredParcelIdRef.current = fid;
                try { map.setFeatureState({ source: 'parcels-bbox', id: fid }, { hover: true }); } catch {}
                map.getCanvas().style.cursor = 'pointer';

                // Tooltip popup
                const props = feat.properties;
                if (hoverPopupRef.current) hoverPopupRef.current.remove();
                const area = props.lot_area_m2 ? `${Math.round(props.lot_area_m2).toLocaleString()} m\u00B2` : '';
                hoverPopupRef.current = new maplibregl.Popup({ closeButton: false, closeOnClick: false, maxWidth: '220px', className: 'parcel-hover-popup' })
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <div style="font-family:Inter,sans-serif;font-size:11px;color:#f0ece4;background:rgba(26,26,26,0.92);backdrop-filter:blur(12px);padding:8px 12px;border-radius:8px;border:1px solid rgba(200,165,92,0.3)">
                            ${props.address ? `<div style="font-weight:600;margin-bottom:3px">${props.address}</div>` : ''}
                            <div style="display:flex;gap:8px;color:#aaa">
                                ${props.zone_code ? `<span style="color:#c8a55c;font-weight:600">${props.zone_code}</span>` : ''}
                                ${area ? `<span>${area}</span>` : ''}
                            </div>
                        </div>
                    `)
                    .addTo(map);
            });

            // Map-level click — uses queryRenderedFeatures so it works through 3D buildings
            map.on('click', (e) => {
                if (map.getZoom() < 15) return;
                const features = map.queryRenderedFeatures(e.point, { layers: ['parcels-bbox-fill'] });
                if (!features.length) return;
                const feat = features[0];
                const props = feat.properties;
                const isMultiSelect = e.originalEvent.metaKey || e.originalEvent.ctrlKey;
                const parcelData = {
                    id: props.id || feat.id,
                    address: props.address || '',
                    zone_code: props.zone_code || '',
                    lot_area_m2: props.lot_area_m2 || 0,
                    geom: feat.geometry,
                };
                if (onParcelClickRef.current) onParcelClickRef.current(parcelData, isMultiSelect);
            });

            // ─── Bbox data loading on moveend ────────────────
            const loadBboxParcels = () => {
                if (bboxDebounceRef.current) clearTimeout(bboxDebounceRef.current);
                bboxDebounceRef.current = setTimeout(async () => {
                    const zoom = map.getZoom();
                    if (zoom < 15) {
                        if (map.getSource('parcels-bbox')) map.getSource('parcels-bbox').setData(EMPTY_FC);
                        return;
                    }
                    if (bboxAbortRef.current) bboxAbortRef.current.abort();
                    const controller = new AbortController();
                    bboxAbortRef.current = controller;
                    try {
                        const fc = await searchParcelsBbox(map.getBounds(), zoom, { signal: controller.signal });
                        if (controller.signal.aborted) return;
                        if (map.getSource('parcels-bbox')) {
                            map.getSource('parcels-bbox').setData(fc);
                            // Re-apply feature-state for selected parcels
                            for (const id of selectedParcelIdsRef.current) {
                                try { map.setFeatureState({ source: 'parcels-bbox', id }, { selected: true }); } catch {}
                            }
                        }
                    } catch {
                        // silently ignore (aborted or network error)
                    }
                }, 300);
            };

            map.on('moveend', loadBboxParcels);

            // ─── Water Main Layers ───────────────────────────
            map.addSource('watermains', { type: 'geojson', data: EMPTY_FC });

            // Dark casing line (wider, behind) — scales with diameter like the fill
            map.addLayer({
                id: 'watermains-line-casing',
                type: 'line',
                source: 'watermains',
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': '#0a0a0a',
                    'line-width': [
                        'interpolate', ['linear'], ['zoom'],
                        12, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 2, 600, 5],
                        16, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 4, 600, 12],
                        19, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 7, 600, 22],
                    ],
                    'line-opacity': 0.55,
                },
            });

            // Colored pipe line — color by material, width by diameter
            map.addLayer({
                id: 'watermains-line',
                type: 'line',
                source: 'watermains',
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': [
                        'match', ['get', 'material'],
                        'CI', '#e67e22',   // Cast Iron → orange (old/legacy)
                        'CICL', '#e67e22',
                        'DIP', '#2277bb',   // Ductile Iron → blue (standard)
                        'DICL', '#2277bb',
                        'PVC', '#27ae60',   // PVC → green (modern)
                        'CPP', '#27ae60',
                        'AC', '#e74c3c',   // Asbestos Cement → red (hazard)
                        'COP', '#f1c40f',   // Copper → yellow
                        '#888888'            // Unknown
                    ],
                    'line-width': [
                        'interpolate', ['linear'], ['zoom'],
                        12, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 0.8, 600, 3],
                        16, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 2, 600, 8],
                        19, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 4, 600, 16],
                    ],
                    'line-opacity': 0.95,
                },
            });

            // Water main labels at higher zoom
            map.addLayer({
                id: 'watermains-label',
                type: 'symbol',
                source: 'watermains',
                minzoom: 15,
                layout: {
                    visibility: 'none',
                    'symbol-placement': 'line',
                    'text-field': ['concat',
                        ['upcase', ['get', 'pipe_type']],
                        ['case', ['has', 'diameter_mm'],
                            ['concat', ' ', ['to-string', ['get', 'diameter_mm']], 'mm'],
                            ''
                        ]
                    ],
                    'text-size': 10,
                    'text-offset': [0, -1],
                    'text-allow-overlap': false,
                },
                paint: {
                    'text-color': '#f0ece4',
                    'text-halo-color': '#1a1a1a',
                    'text-halo-width': 1.5,
                },
            });

            // ─── Sewer Layers ───────────────────────────
            map.addSource('sewers', { type: 'geojson', data: EMPTY_FC });

            map.addLayer({
                id: 'sewers-line-casing',
                type: 'line',
                source: 'sewers',
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': '#0a0a0a',
                    'line-width': ['interpolate', ['linear'], ['zoom'],
                        12, 2, 16, 4, 19, 8],
                    'line-opacity': 0.45,
                },
            });

            map.addLayer({
                id: 'sewers-line',
                type: 'line',
                source: 'sewers',
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': [
                        'match', ['get', 'pipe_type'],
                        'sanitary_sewer', '#886644',
                        'storm_sewer', '#44aa66',
                        '#886644'
                    ],
                    'line-width': ['interpolate', ['linear'], ['zoom'],
                        12, 1, 16, 3, 19, 6],
                    'line-opacity': 0.9,
                },
            });

            // ─── Electrical Layers ───────────────────────────
            map.addSource('electrical', { type: 'geojson', data: EMPTY_FC });

            map.addLayer({
                id: 'electrical-line',
                type: 'line',
                source: 'electrical',
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': ['coalesce', ['get', 'voltage_color'], '#ddaa22'],
                    'line-width': ['interpolate', ['linear'], ['zoom'],
                        12, ['*', ['coalesce', ['get', 'line_width_factor'], 1], 1],
                        16, ['*', ['coalesce', ['get', 'line_width_factor'], 1], 2],
                        19, ['*', ['coalesce', ['get', 'line_width_factor'], 1], 4]
                    ],
                    'line-opacity': 0.85,
                },
            });

            // ─── Click handlers for infrastructure ─────────
            const infraClickHandler = (layerId) => (e) => {
                if (!e.features?.length) return;
                const props = e.features[0].properties;
                if (popupRef.current) popupRef.current.remove();
                const label = (props.pipe_type || props.asset_type || '').replace(/_/g, ' ');
                popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '260px' })
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <div style="font-family:Inter,sans-serif;font-size:12px;color:#1a1a1a">
                            <strong style="text-transform:capitalize">${label}</strong><br/>
                            ${props.location ? `<span style="color:#555">${props.location}</span><br/>` : ''}
                            ${props.diameter_mm ? `Diameter: ${props.diameter_mm}mm<br/>` : ''}
                            ${props.voltage_kv ? `Voltage: ${props.voltage_kv} kV<br/>` : ''}
                            ${props.material ? `Material: ${props.material}<br/>` : ''}
                            ${props.install_year ? `Installed: ${props.install_year}<br/>` : ''}
                            ${props.operator ? `Operator: ${props.operator}<br/>` : ''}
                            ${props.distance_m ? `<span style="color:#888">${props.distance_m}m away</span>` : ''}
                        </div>
                    `)
                    .addTo(map);
            };

            for (const layerId of ['watermains-line', 'sewers-line', 'electrical-line']) {
                map.on('click', layerId, infraClickHandler(layerId));
                map.on('mouseenter', layerId, () => { map.getCanvas().style.cursor = 'pointer'; });
                map.on('mouseleave', layerId, () => { map.getCanvas().style.cursor = ''; });
            }
        });

        return () => {
            map.remove();
            mapInstanceRef.current = null;
        };
    }, []);

    return (
        <>
            <div id="map" ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '400px' }} />

            {isParcelResolved && !isModelOpen && (
                <button
                    className="map-model-btn"
                    onClick={onModelOpen}
                    title="View 3D Model"
                    aria-label="View 3D Model"
                    style={{
                        right: `${(isPanelOpen ? 380 : 0) + 16}px`,
                        bottom: `${chatPanelHeight + 16}px`,
                    }}
                >
                    ⬡ Model
                </button>
            )}
        </>
    );
});

export default MapView;
