import { useEffect, useRef, useImperativeHandle, forwardRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import '../ModelViewer.css';

const DEFAULT_CENTER = [-79.3832, 43.6532];
const DEFAULT_ZOOM = 13;

const MapView = forwardRef(function MapView({ isParcelResolved, onModelOpen, isPanelOpen, isSidebarCollapsed, isChatExpanded, isModelOpen }, ref) {
    const containerRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const markerRef = useRef(null);
    const [mapLoaded, setMapLoaded] = useState(false);

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
                map.getSource('parcel').setData(geojson || { type: 'FeatureCollection', features: [] });
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
                map.getSource('proposed-massing').setData(geojson || { type: 'FeatureCollection', features: [] });
            }

            if (height_m && geojson) {
                map.setPaintProperty('proposed-massing-extrusion', 'fill-extrusion-height', height_m);
                map.flyTo({
                    pitch: 60,
                    bearing: 20,
                    duration: 3000,
                    essential: true
                });

                // Hide overlapping OSM buildings by finding ones under the new shape
                // We'll calculate a bounding box or just use feature querying if we want to be exact.
                // For simplicity, we can let them overlap or rely on z-indexing, but we can also just 
                // hide all background buildings if that is easiest by setting opacity down or using spatial filter elsewhere.
            } else if (geojson === null) {
                // Only reset camera if explicitly clearing massing after it was shown
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
        }
    }));

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
                    // Hide POI labels (store names, restaurants, etc.)
                    if (layer.id.includes('poi') || layer.id.includes('shop') || layer.id.includes('amenity')) {
                        map.setLayoutProperty(layer.id, 'visibility', 'none');
                    }
                    // Show housenumber labels prominently
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

            // Add OSM 3D buildings Layer First (Background Context)
            map.addLayer({
                'id': 'osm-buildings-3d',
                'source': 'openmaptiles',
                'source-layer': 'building',
                'type': 'fill-extrusion',
                'minzoom': 14,
                'paint': {
                    'fill-extrusion-color': '#e0e0e0', // Neutral grey
                    'fill-extrusion-height': ['get', 'render_height'],
                    'fill-extrusion-base': ['get', 'render_min_height'],
                    'fill-extrusion-opacity': 0.6
                }
            });

            // Add source for parcel outline
            map.addSource('parcel', {
                type: 'geojson',
                data: pendingParcelRef.current || { type: 'FeatureCollection', features: [] }
            });

            // Add fill layer for parcel
            map.addLayer({
                id: 'parcel-fill',
                type: 'fill',
                source: 'parcel',
                paint: {
                    'fill-color': '#c8a55c',
                    'fill-opacity': 0.2
                }
            });

            // Add line layer for parcel
            map.addLayer({
                id: 'parcel-line',
                type: 'line',
                source: 'parcel',
                paint: {
                    'line-color': '#c8a55c',
                    'line-width': 2
                }
            });

            // Add source for proposed massing
            const pendingM = pendingMassingRef.current;
            map.addSource('proposed-massing', {
                type: 'geojson',
                data: pendingM?.geojson || { type: 'FeatureCollection', features: [] }
            });

            // Add fill-extrusion layer for proposed massing
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
