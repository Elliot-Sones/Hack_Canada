import { getShortAddress, getZoneLabel } from '../lib/parcelState.js';

export default function SelectionChips({ parcels, primaryId, onSetPrimary, onRemove, onClearAll, isSidebarCollapsed }) {
    if (!parcels || parcels.length === 0) return null;

    return (
        <div className={`selection-chips-bar${isSidebarCollapsed ? ' sidebar-collapsed' : ''}`}>
            {parcels.map((p) => {
                const isPrimary = p.id === primaryId;
                return (
                    <div
                        key={p.id}
                        className={`selection-chip${isPrimary ? ' selection-chip--primary' : ''}`}
                        onClick={() => onSetPrimary(p.id)}
                        title={isPrimary ? 'Primary parcel' : 'Click to set as primary'}
                    >
                        <span className="selection-chip-zone">{getZoneLabel(p)}</span>
                        <span className="selection-chip-addr">{getShortAddress(p)}</span>
                        <button
                            className="selection-chip-remove"
                            onClick={(e) => { e.stopPropagation(); onRemove(p.id); }}
                            title="Remove"
                        >
                            ×
                        </button>
                    </div>
                );
            })}
            {parcels.length >= 2 && (
                <button className="selection-chips-clear" onClick={onClearAll}>
                    Clear all
                </button>
            )}
        </div>
    );
}
