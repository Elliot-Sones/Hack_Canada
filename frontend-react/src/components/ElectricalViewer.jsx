import { useState, useCallback, useMemo } from 'react';
import '../ElectricalViewer.css';

const VOLTAGE_TIERS = [
    { key: '500kV', label: '500 kV Transmission', color: '#e74c3c' },
    { key: '115kV', label: '115 kV Transmission', color: '#e67e22' },
    { key: '27kV', label: '27.6 kV Distribution', color: '#3498db' },
    { key: '13kV', label: '13.8 kV Distribution', color: '#2ecc71' },
    { key: 'local', label: 'Local Secondary', color: '#f1c40f' },
    { key: 'unknown', label: 'Unknown (Distribution)', color: '#9b59b6' },
];

const LAYER_LABELS = {
    power_line: 'Power Lines',
    electrical_substation: 'Substations',
};

export default function ElectricalViewer({ isOpen, onClose, isPanelOpen, isSidebarCollapsed, isChatExpanded, electricalData, mapCenter }) {
    const [layerVisibility, setLayerVisibility] = useState({
        power_line: true,
        electrical_substation: true,
    });

    const stats = useMemo(() => {
        const features = electricalData?.features || [];
        const lines = features.filter(f => f.properties?.layer_type === 'power_line');
        const subs = features.filter(f => f.properties?.layer_type === 'electrical_substation');
        const transformers = features.filter(f =>
            (f.properties?.power_type || '').toLowerCase().includes('transformer')
        );
        return {
            totalLines: lines.length,
            totalSubs: subs.length,
            totalTransformers: transformers.length,
        };
    }, [electricalData]);

    const toggleLayer = useCallback((layerType) => {
        setLayerVisibility(prev => ({ ...prev, [layerType]: !prev[layerType] }));
    }, []);

    if (!isOpen) return null;

    return (
        <div className="elec-viewer-overlay">
            <button className="elec-close-btn" onClick={onClose} title="Close Electrical Viewer">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="20" height="20">
                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                </svg>
            </button>

            {/* Stats Bar */}
            <div className="elec-stats-bar">
                <div className="elec-stat">
                    <span className="elec-stat-value">{stats.totalLines.toLocaleString()}</span>
                    <span className="elec-stat-label">Power Lines</span>
                </div>
                <div className="elec-stat">
                    <span className="elec-stat-value">{stats.totalSubs.toLocaleString()}</span>
                    <span className="elec-stat-label">Substations</span>
                </div>
                <div className="elec-stat">
                    <span className="elec-stat-value">{stats.totalTransformers.toLocaleString()}</span>
                    <span className="elec-stat-label">Transformers</span>
                </div>
            </div>

            {/* Layer toggles + Voltage Legend */}
            <div className="elec-filter-panel">
                <div className="elec-filter-header">Layers</div>
                {Object.entries(LAYER_LABELS).map(([key, label]) => (
                    <label key={key} className="elec-filter-item">
                        <input
                            type="checkbox"
                            checked={layerVisibility[key]}
                            onChange={() => toggleLayer(key)}
                        />
                        {label}
                    </label>
                ))}

                <div className="elec-filter-header" style={{ marginTop: 14 }}>Voltage Tiers</div>
                {VOLTAGE_TIERS.map(tier => (
                    <div key={tier.key} className="elec-legend-item">
                        <span className="elec-legend-line" style={{ background: tier.color }} />
                        <span>{tier.label}</span>
                    </div>
                ))}
                <div className="elec-filter-header" style={{ marginTop: 10 }}>Nodes</div>
                <div className="elec-legend-item">
                    <span className="elec-legend-dot elec-legend-dot--lg" style={{ background: '#8e44ad' }} />
                    <span>Substation</span>
                </div>
                <div className="elec-legend-item">
                    <span className="elec-legend-dot" style={{ background: '#8e44ad', opacity: 0.6 }} />
                    <span>Transformer</span>
                </div>
            </div>
        </div>
    );
}
