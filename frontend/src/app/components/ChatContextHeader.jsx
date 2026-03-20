import { getShortAddress, getZoneLabel } from '../lib/parcelState';

export default function ChatContextHeader({ selectedParcels, primaryParcel, analyzedUploads, activePlanId, isExpanded, onGenerateReport }) {
    if (!isExpanded || !selectedParcels || selectedParcels.length === 0) return null;

    const primaryId = primaryParcel?.id;

    return (
        <div className="chat-context-header">
            <div className="chat-context-items">
                {selectedParcels.map((p) => {
                    const isPrimary = p.id === primaryId;
                    const zone = getZoneLabel(p);
                    const addr = getShortAddress(p);
                    return (
                        <span key={p.id} className={`chat-ctx-parcel${isPrimary ? ' chat-ctx-primary' : ''}`}>
                            {zone && <span className="chat-ctx-zone">{zone}</span>}
                            {!zone && p.status === 'unresolved' && <span className="chat-ctx-warn">&#x26A0;</span>}
                            <span className="chat-ctx-addr">{addr}</span>
                            {isPrimary && <span className="chat-ctx-tag">primary</span>}
                        </span>
                    );
                })}
                {analyzedUploads?.map((u) => (
                    <span key={u.id || u.filename} className="chat-ctx-indicator">{u.filename}</span>
                ))}
                {activePlanId && <span className="chat-ctx-indicator">Plan active</span>}
            </div>
            {onGenerateReport && (
                <button className="chat-ctx-report-btn" onClick={onGenerateReport} title="Generate report">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                        <line x1="16" y1="13" x2="8" y2="13"/>
                        <line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                </button>
            )}
        </div>
    );
}
