import { useState, useEffect, useRef } from 'react';
import { getNearbyPipelines, getElectricalNearby } from '../api.js';
import { extractCentroid } from '../lib/geoUtils.js';
import { isResolvedParcel } from '../lib/parcelState.js';

const EMPTY_FC = { type: 'FeatureCollection', features: [] };

/**
 * Fetches nearby infrastructure (water, sanitary, storm, electrical) for a parcel.
 * Returns { infraData, infraLoading } where infraData has { water, sanitary, storm, electrical, centroid }.
 */
export default function useNearbyInfrastructure(parcel) {
    const [infraData, setInfraData] = useState(null);
    const [infraLoading, setInfraLoading] = useState(false);
    const abortRef = useRef(null);

    useEffect(() => {
        if (abortRef.current) abortRef.current.abort();

        if (!isResolvedParcel(parcel) || !parcel.geom) {
            setInfraData(null);
            setInfraLoading(false);
            return;
        }

        const centroid = extractCentroid(parcel.geom);
        if (!centroid) {
            setInfraData(null);
            setInfraLoading(false);
            return;
        }

        const [lng, lat] = centroid;
        const controller = new AbortController();
        abortRef.current = controller;
        setInfraLoading(true);

        Promise.allSettled([
            getNearbyPipelines(lat, lng, 500, 'water_main', { signal: controller.signal }),
            getNearbyPipelines(lat, lng, 500, 'sanitary_sewer', { signal: controller.signal }),
            getNearbyPipelines(lat, lng, 500, 'storm_sewer', { signal: controller.signal }),
            getElectricalNearby(lat, lng, 500, { signal: controller.signal }),
        ]).then(([water, sanitary, storm, electrical]) => {
            if (controller.signal.aborted) return;
            setInfraData({
                water: water.status === 'fulfilled' ? water.value : EMPTY_FC,
                sanitary: sanitary.status === 'fulfilled' ? sanitary.value : EMPTY_FC,
                storm: storm.status === 'fulfilled' ? storm.value : EMPTY_FC,
                electrical: electrical.status === 'fulfilled' ? electrical.value : EMPTY_FC,
                centroid,
            });
            setInfraLoading(false);
        });

        return () => controller.abort();
    }, [parcel?.id, parcel?.geom]);

    return { infraData, infraLoading };
}
