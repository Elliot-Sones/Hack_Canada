import { useState } from 'react';
import { checkElectricalCapacity } from '../api.js';

const SYSTEMS = [
    { key: 'water', label: 'Water', icon: '💧', pipeTypeField: 'pipe_type', valuePrefix: 'water_main' },
    { key: 'sanitary', label: 'Sanitary', icon: '🔧', pipeTypeField: 'pipe_type', valuePrefix: 'sanitary_sewer' },
    { key: 'storm', label: 'Storm', icon: '🌧', pipeTypeField: 'pipe_type', valuePrefix: 'storm_sewer' },
    { key: 'electrical', label: 'Electrical', icon: '⚡', isElectrical: true },
];

function getStatus(features) {
    if (!features || features.length === 0) return { level: 'unknown', label: 'No Data', color: 'var(--text-muted, #888)' };
    const nearest = features[0];
    const dist = nearest.properties?.distance_m;
    if (dist == null) return { level: 'unknown', label: 'Unknown', color: 'var(--text-muted, #888)' };
    if (dist < 100) return { level: 'adequate', label: 'Adequate', color: '#22c55e' };
    if (dist <= 500) return { level: 'review', label: 'Review Needed', color: '#eab308' };
    return { level: 'insufficient', label: 'Insufficient', color: '#ef4444' };
}

function formatPipeSummary(feature) {
    if (!feature) return 'No nearby assets';
    const p = feature.properties || {};
    const parts = [];
    if (p.diameter_mm) parts.push(`${p.diameter_mm}mm`);
    if (p.material) parts.push(p.material);
    if (p.distance_m != null) parts.push(`${Math.round(p.distance_m)}m away`);
    if (p.install_year) parts.push(String(p.install_year));
    return parts.join(', ') || 'Details unavailable';
}

function formatElectricalSummary(feature) {
    if (!feature) return 'No nearby assets';
    const p = feature.properties || {};
    const parts = [];
    if (p.voltage_kv) parts.push(`${p.voltage_kv} kV`);
    if (p.asset_type) parts.push(p.asset_type.replace(/_/g, ' '));
    if (p.distance_m != null) parts.push(`${Math.round(p.distance_m)}m`);
    return parts.join(', ') || 'Details unavailable';
}

const BUILDING_TYPES = [
    { value: 'residential_lowrise', label: 'Residential Low-Rise' },
    { value: 'residential_midrise', label: 'Residential Mid-Rise' },
    { value: 'residential_highrise', label: 'Residential High-Rise' },
    { value: 'commercial_office', label: 'Commercial Office' },
    { value: 'commercial_retail', label: 'Commercial Retail' },
    { value: 'mixed_use', label: 'Mixed Use' },
    { value: 'industrial', label: 'Industrial' },
];

function CapacityCheckForm({ parcelCentroid, onResult }) {
    const [form, setForm] = useState({
        building_type: 'residential_midrise',
        num_units: 50,
        total_area_m2: 5000,
        num_floors: 6,
        has_ev_charging: false,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!parcelCentroid) return;
        setLoading(true);
        setError(null);
        try {
            const result = await checkElectricalCapacity({
                lat: parcelCentroid[1],
                lng: parcelCentroid[0],
                ...form,
            });
            onResult(result);
        } catch (err) {
            setError(err.message || 'Capacity check failed');
        } finally {
            setLoading(false);
        }
    };

    const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }));

    return (
        <form onSubmit={handleSubmit} style={{ marginTop: 12 }}>
            <div className="zoning-limits-grid">
                <label className="zoning-limit-card" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span className="dd-card-label">Building Type</span>
                    <select className="config-input" value={form.building_type}
                        onChange={e => update('building_type', e.target.value)}>
                        {BUILDING_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select>
                </label>
                <label className="zoning-limit-card" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span className="dd-card-label">Units</span>
                    <input className="config-input" type="number" min={1} value={form.num_units}
                        onChange={e => update('num_units', parseInt(e.target.value) || 1)} />
                </label>
                <label className="zoning-limit-card" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span className="dd-card-label">Area (m²)</span>
                    <input className="config-input" type="number" min={1} value={form.total_area_m2}
                        onChange={e => update('total_area_m2', parseInt(e.target.value) || 1)} />
                </label>
                <label className="zoning-limit-card" style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    <span className="dd-card-label">Floors</span>
                    <input className="config-input" type="number" min={1} value={form.num_floors}
                        onChange={e => update('num_floors', parseInt(e.target.value) || 1)} />
                </label>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '8px 0', fontSize: 13, color: 'var(--text-secondary)' }}>
                <input type="checkbox" checked={form.has_ev_charging}
                    onChange={e => update('has_ev_charging', e.target.checked)} />
                EV Charging Stations
            </label>
            <button type="submit" className="tag" disabled={loading}
                style={{ cursor: 'pointer', padding: '6px 16px', marginTop: 4, opacity: loading ? 0.6 : 1 }}>
                {loading ? 'Checking…' : 'Check Capacity'}
            </button>
            {error && <p style={{ color: '#ef4444', fontSize: 13, marginTop: 8 }}>{error}</p>}
        </form>
    );
}

function CapacityResult({ result }) {
    if (!result) return null;
    const verdictColors = {
        adequate: '#22c55e',
        marginal: '#eab308',
        insufficient: '#ef4444',
    };
    const color = verdictColors[result.verdict] || 'var(--text-muted)';

    return (
        <div className="dd-card" style={{ marginTop: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: color }} />
                <span className="dd-card-label" style={{ margin: 0 }}>
                    {(result.verdict || 'unknown').charAt(0).toUpperCase() + (result.verdict || 'unknown').slice(1)}
                </span>
            </div>
            <div className="zoning-limits-grid">
                {result.estimated_demand_kw != null && (
                    <div className="zoning-limit-card">
                        <div className="dd-card-label">Est. Demand</div>
                        <div className="dd-card-value">{Math.round(result.estimated_demand_kw)} kW</div>
                    </div>
                )}
                {result.infrastructure_score != null && (
                    <div className="zoning-limit-card">
                        <div className="dd-card-label">Infra Score</div>
                        <div className="dd-card-value">{result.infrastructure_score}/100</div>
                    </div>
                )}
            </div>
            {result.recommendations?.length > 0 && (
                <ul style={{ margin: '10px 0 0 18px', padding: 0 }}>
                    {result.recommendations.map((rec, i) => (
                        <li key={i} style={{ marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>{rec}</li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default function ServicingSummaryCard({ infraData, infraLoading, parcelCentroid }) {
    const [showCapacityForm, setShowCapacityForm] = useState(false);
    const [capacityResult, setCapacityResult] = useState(null);

    if (infraLoading) {
        return (
            <div className="dd-card" style={{ marginTop: 16 }}>
                <div className="dd-card-label">Municipal Servicing</div>
                <p className="tab-section-desc">Loading nearby infrastructure…</p>
                <div className="zoning-limits-grid">
                    {[1, 2, 3, 4].map(i => (
                        <div key={i} className="zoning-limit-card" style={{ minHeight: 56, opacity: 0.4, animation: 'pulse 1.5s infinite' }} />
                    ))}
                </div>
            </div>
        );
    }

    if (!infraData) return null;

    const allEmpty = SYSTEMS.every(s => {
        const fc = infraData[s.key];
        return !fc?.features || fc.features.length === 0;
    });

    if (allEmpty) {
        return (
            <div className="dd-card" style={{ marginTop: 16 }}>
                <div className="dd-card-label">Municipal Servicing</div>
                <p className="tab-section-desc" style={{ opacity: 0.6 }}>
                    No infrastructure data available for this parcel.
                </p>
            </div>
        );
    }

    return (
        <div style={{ marginTop: 16 }}>
            <div className="tab-section-header">
                <h3>Municipal Servicing</h3>
                <p className="tab-section-desc">Nearby infrastructure within 500m</p>
            </div>

            <div className="zoning-limits-grid">
                {SYSTEMS.map(sys => {
                    const fc = infraData[sys.key];
                    const features = fc?.features || [];
                    const status = getStatus(features);
                    const nearest = features[0];
                    const summary = sys.isElectrical
                        ? formatElectricalSummary(nearest)
                        : formatPipeSummary(nearest);

                    return (
                        <div key={sys.key} className="zoning-limit-card">
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                                <span style={{
                                    display: 'inline-block', width: 8, height: 8,
                                    borderRadius: '50%', background: status.color, flexShrink: 0,
                                }} />
                                <span className="dd-card-label" style={{ margin: 0 }}>{sys.label}</span>
                            </div>
                            <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                                {summary}
                            </div>
                            <div style={{ fontSize: 11, marginTop: 4, color: status.color, fontWeight: 600 }}>
                                {status.label}
                            </div>
                        </div>
                    );
                })}
            </div>

            <button
                className="tag"
                style={{ cursor: 'pointer', padding: '6px 16px', marginTop: 8 }}
                onClick={() => { setShowCapacityForm(prev => !prev); setCapacityResult(null); }}
            >
                {showCapacityForm ? 'Hide Capacity Check' : 'Run Capacity Check'}
            </button>

            {showCapacityForm && (
                <CapacityCheckForm parcelCentroid={parcelCentroid} onResult={setCapacityResult} />
            )}
            <CapacityResult result={capacityResult} />
        </div>
    );
}
