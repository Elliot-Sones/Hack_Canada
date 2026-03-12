import { useEffect, useRef, useImperativeHandle, forwardRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../ModelViewer.css';

const DEFAULT_CENTER = [-79.3832, 43.6532];
const DEFAULT_ZOOM = 13;

const EMPTY_FC = { type: 'FeatureCollection', features: [] };

const PIPE_COLORS = {
    water_main: '#2277bb',
    sanitary_sewer: '#886644',
    storm_sewer: '#44aa66',
    gas_line: '#ddaa22',
};

const MapView = forwardRef(function MapView({ isParcelResolved, onModelOpen, isPanelOpen, isSidebarCollapsed, isChatExpanded, isModelOpen, assetType, onInfraAssetClick }, ref) {
    const containerRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markerRef = useRef(null);
    const popupRef = useRef(null);
    const [mapLoaded, setMapLoaded] = useState(false);
    const onInfraAssetClickRef = useRef(onInfraAssetClick);
    useEffect(() => { onInfraAssetClickRef.current = onInfraAssetClick; }, [onInfraAssetClick]);

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
        /** Load pipeline GeoJSON onto the map */
        setPipelines(geojson) {
            const map = mapInstanceRef.current;
            if (!map || !mapLoaded) return;
            const fc = geojson || EMPTY_FC;
            if (map.getSource('pipelines')) {
                map.getSource('pipelines').setData(fc);
            }
            setInfraEmpty(!fc.features || fc.features.length === 0);
        },
        /** Load electrical GeoJSON onto the map */
        setElectrical(geojson) {
            const map = mapInstanceRef.current;
            if (!map || !mapLoaded) return;
            const fc = geojson || EMPTY_FC;
            if (map.getSource('electrical')) {
                map.getSource('electrical').setData(fc);
            }
            setInfraEmpty(!fc.features || fc.features.length === 0);
        },
    }));

    // Track whether infra data has been loaded
    const [infraEmpty, setInfraEmpty] = useState(false);

    // Toggle layer visibility and camera based on asset type
    useEffect(() => {
        const map = mapInstanceRef.current;
        if (!map || !mapLoaded) return;

        const pipelineLayers = ['pipelines-line', 'pipelines-line-casing', 'pipelines-label'];
        const electricalLayers = ['electrical-lines', 'electrical-lines-casing', 'electrical-substations', 'electrical-labels'];

        // Buildings: always visible but dimmer in infra mode to give 3D context
        const isInfra = assetType === 'pipeline' || assetType === 'electrical';
        if (map.getLayer('osm-buildings-3d')) {
            map.setLayoutProperty('osm-buildings-3d', 'visibility', 'visible');
            map.setPaintProperty('osm-buildings-3d', 'fill-extrusion-opacity', isInfra ? 0.25 : 0.6);
            map.setPaintProperty('osm-buildings-3d', 'fill-extrusion-color', isInfra ? '#aaaaaa' : '#e0e0e0');
        }
        for (const id of ['parcel-fill', 'parcel-line', 'proposed-massing-extrusion']) {
            if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', assetType === 'building' ? 'visible' : 'none');
        }
        for (const id of pipelineLayers) {
            if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', assetType === 'pipeline' ? 'visible' : 'none');
        }
        for (const id of electricalLayers) {
            if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', assetType === 'electrical' ? 'visible' : 'none');
        }

        // Camera
        if (assetType === 'pipeline' || assetType === 'electrical') {
            map.easeTo({ pitch: 55, bearing: -20, duration: 1200 });
            setInfraEmpty(true);
        } else {
            map.easeTo({ pitch: 0, bearing: 0, duration: 800 });
            setInfraEmpty(false);
        }
    }, [assetType, mapLoaded]);

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
                    'fill-extrusion-opacity': 0.6
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

            // ─── Pipeline Layers ───────────────────────────
            map.addSource('pipelines', { type: 'geojson', data: EMPTY_FC });

            // Dark casing line (wider, behind) — scales with diameter like the fill
            map.addLayer({
                id: 'pipelines-line-casing',
                type: 'line',
                source: 'pipelines',
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
                id: 'pipelines-line',
                type: 'line',
                source: 'pipelines',
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': ['coalesce', ['get', 'color'], '#888888'],
                    'line-width': [
                        'interpolate', ['linear'], ['zoom'],
                        12, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 0.8, 600, 3],
                        16, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 2, 600, 8],
                        19, ['interpolate', ['linear'], ['coalesce', ['get', 'diameter_mm'], 150], 50, 4, 600, 16],
                    ],
                    'line-opacity': 0.95,
                },
            });

            // Pipeline labels at higher zoom
            map.addLayer({
                id: 'pipelines-label',
                type: 'symbol',
                source: 'pipelines',
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

            // ─── Electrical Layers ────────────────────────────
            map.addSource('electrical', { type: 'geojson', data: EMPTY_FC });

            // Casing (dark outline behind power lines)
            map.addLayer({
                id: 'electrical-lines-casing',
                type: 'line',
                source: 'electrical',
                filter: ['in', ['get', 'layer_type'], ['literal', ['power_line']]],
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': '#0a0a0a',
                    'line-width': ['interpolate', ['linear'], ['zoom'], 10, 2, 14, 4, 18, 8],
                    'line-opacity': 0.4,
                },
            });

            // Power lines — colored by voltage_color property from backend
            map.addLayer({
                id: 'electrical-lines',
                type: 'line',
                source: 'electrical',
                filter: ['in', ['get', 'layer_type'], ['literal', ['power_line']]],
                layout: { visibility: 'none', 'line-cap': 'round', 'line-join': 'round' },
                paint: {
                    'line-color': ['coalesce', ['get', 'voltage_color'], '#e74c3c'],
                    'line-width': [
                        'interpolate', ['linear'], ['zoom'],
                        10, ['*', 1.0, ['coalesce', ['get', 'line_width_factor'], 1]],
                        14, ['*', 2.5, ['coalesce', ['get', 'line_width_factor'], 1]],
                        18, ['*', 5, ['coalesce', ['get', 'line_width_factor'], 1]],
                    ],
                    'line-opacity': 0.9,
                },
            });

            // Substations as circles
            map.addLayer({
                id: 'electrical-substations',
                type: 'circle',
                source: 'electrical',
                filter: ['in', ['get', 'layer_type'], ['literal', ['electrical_substation']]],
                layout: { visibility: 'none' },
                paint: {
                    'circle-radius': ['interpolate', ['linear'], ['zoom'], 10, 4, 14, 8, 18, 14],
                    'circle-color': '#8e44ad',
                    'circle-stroke-color': '#1a1a1a',
                    'circle-stroke-width': 1.5,
                    'circle-opacity': 0.85,
                },
            });

            // Labels for power lines
            map.addLayer({
                id: 'electrical-labels',
                type: 'symbol',
                source: 'electrical',
                filter: ['in', ['get', 'layer_type'], ['literal', ['power_line']]],
                minzoom: 15,
                layout: {
                    visibility: 'none',
                    'symbol-placement': 'line',
                    'text-field': ['case',
                        ['has', 'voltage_tier'],
                        ['concat', ['upcase', ['get', 'voltage_tier']], ' Line'],
                        'Power Line'
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

            // Click handlers for electrical features
            map.on('click', 'electrical-lines', (e) => {
                if (!e.features?.length) return;
                const props = e.features[0].properties;
                if (popupRef.current) popupRef.current.remove();
                popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '260px' })
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <div style="font-family:Inter,sans-serif;font-size:12px;color:#1a1a1a">
                            <strong>Power Line</strong><br/>
                            ${props.voltage_tier && props.voltage_tier !== 'unknown' ? `Voltage: ${props.voltage_tier}<br/>` : ''}
                            ${props.voltage_kv ? `${props.voltage_kv} kV<br/>` : ''}
                            ${props.name ? `${props.name}<br/>` : ''}
                        </div>
                    `)
                    .addTo(map);
            });

            map.on('click', 'electrical-substations', (e) => {
                if (!e.features?.length) return;
                const props = e.features[0].properties;
                if (popupRef.current) popupRef.current.remove();
                popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '260px' })
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <div style="font-family:Inter,sans-serif;font-size:12px;color:#1a1a1a">
                            <strong>Substation</strong><br/>
                            ${props.name ? `${props.name}<br/>` : ''}
                            ${props.voltage ? `Voltage: ${props.voltage}<br/>` : ''}
                            ${props.power_type ? `Type: ${props.power_type}<br/>` : ''}
                        </div>
                    `)
                    .addTo(map);
            });

            map.on('mouseenter', 'electrical-lines', () => { map.getCanvas().style.cursor = 'pointer'; });
            map.on('mouseleave', 'electrical-lines', () => { map.getCanvas().style.cursor = ''; });
            map.on('mouseenter', 'electrical-substations', () => { map.getCanvas().style.cursor = 'pointer'; });
            map.on('mouseleave', 'electrical-substations', () => { map.getCanvas().style.cursor = ''; });

            // ─── Click handlers for infrastructure ─────────
            map.on('click', 'pipelines-line', (e) => {
                if (!e.features?.length) return;
                const props = e.features[0].properties;
                if (popupRef.current) popupRef.current.remove();
                const label = (props.pipe_type || '').replace(/_/g, ' ');
                popupRef.current = new maplibregl.Popup({ closeButton: true, maxWidth: '260px' })
                    .setLngLat(e.lngLat)
                    .setHTML(`
                        <div style="font-family:Inter,sans-serif;font-size:12px;color:#1a1a1a">
                            <strong style="text-transform:capitalize">${label}</strong><br/>
                            ${props.location ? `<span style="color:#555">${props.location}</span><br/>` : ''}
                            ${props.diameter_mm ? `Diameter: ${props.diameter_mm}mm<br/>` : ''}
                            ${props.material ? `Material: ${props.material}<br/>` : ''}
                            ${props.install_year ? `Installed: ${props.install_year}<br/>` : ''}
                            ${props.length_m ? `Length: ${props.length_m}m<br/>` : ''}
                            ${props.depth_m ? `Depth: ${props.depth_m}m<br/>` : ''}
                            ${props.distance_m ? `<span style="color:#888">${props.distance_m}m away</span>` : ''}
                        </div>
                    `)
                    .addTo(map);
                if (onInfraAssetClickRef.current) onInfraAssetClickRef.current({ type: 'pipeline', ...props });
            });

            // Cursor styling for interactive layers
            map.on('mouseenter', 'pipelines-line', () => { map.getCanvas().style.cursor = 'pointer'; });
            map.on('mouseleave', 'pipelines-line', () => { map.getCanvas().style.cursor = ''; });
        });

        return () => {
            map.remove();
            mapInstanceRef.current = null;
        };
    }, []);

    const MODE_LABELS = { building: null, pipeline: 'Pipeline Network', electrical: 'Electrical Grid' };
    const MODE_ICONS = { pipeline: '⏣', electrical: '⚡' };
    const MODE_COLORS = { pipeline: '#44aa66', electrical: '#e74c3c' };

    return (
        <>
            <div id="map" ref={containerRef} style={{ width: '100%', height: '100%', minHeight: '400px' }} />

            {/* Infrastructure mode banner */}
            {assetType !== 'building' && (
                <div style={{
                    position: 'absolute', top: 12, left: '50%', transform: 'translateX(-50%)',
                    background: '#1a1a1a', border: `1px solid ${MODE_COLORS[assetType]}`,
                    borderRadius: 8, padding: '8px 20px', zIndex: 20,
                    display: 'flex', alignItems: 'center', gap: 8,
                    fontFamily: 'Inter, sans-serif', fontSize: 13, color: '#f0ece4',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.5)', pointerEvents: 'none',
                }}>
                    <span style={{ fontSize: 18 }}>{MODE_ICONS[assetType]}</span>
                    <span style={{ color: MODE_COLORS[assetType], fontWeight: 600 }}>{MODE_LABELS[assetType]}</span>
                    <span style={{ display: 'flex', gap: 10, marginLeft: 4, alignItems: 'center' }}>
                        {assetType === 'pipeline' && [['Water Main', '#2277bb'], ['Sanitary', '#886644'], ['Storm', '#44aa66']].map(([label, color]) => (
                            <span key={label} style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 10, color: '#ccc' }}>
                                <span style={{ width: 16, height: 3, background: color, borderRadius: 2, display: 'inline-block' }} />
                                {label}
                            </span>
                        ))}
                    </span>
                </div>
            )}

            {/* Empty state for infrastructure */}
            {assetType !== 'building' && infraEmpty && (
                <div style={{
                    position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
                    background: 'rgba(26,26,26,0.92)', borderRadius: 12, padding: '32px 40px',
                    zIndex: 15, textAlign: 'center', maxWidth: 360,
                    fontFamily: 'Inter, sans-serif', color: '#f0ece4',
                    boxShadow: '0 8px 32px rgba(0,0,0,0.6)', border: '1px solid #333',
                }}>
                    <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.6 }}>⏣</div>
                    <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 8 }}>
                        No infrastructure data in this area
                    </div>
                    <div style={{ fontSize: 12, color: '#888', lineHeight: 1.5 }}>
                        Pan or zoom the map to load water main and sewer data.
                    </div>
                </div>
            )}

            {isParcelResolved && !isModelOpen && (
                <button
                    className="map-model-btn"
                    onClick={onModelOpen}
                    title="Open 3D Model"
                    style={{
                        right: `${(isPanelOpen ? 380 : 0) + 16}px`,
                        bottom: `${(isChatExpanded ? 328 : 48) + 16}px`,
                        transition: 'right 0.3s ease, bottom 0.3s ease',
                    }}
                >
                    ⬡ Model
                </button>
            )}
        </>
    );
});

export default MapView;
