import { useState, useCallback } from 'react';

// DB-backed infrastructure layers (fetched via API)
const DB_INFRA_LAYERS = [
  { id: 'watermains', label: 'Water Mains', color: '#2277bb', icon: '\u{1F4A7}' },
  { id: 'sewers', label: 'Sewers', color: '#886644', icon: '\u{1F527}' },
  { id: 'electrical', label: 'Electrical Grid', color: '#ddaa22', icon: '\u26A1' },
];

export default function InfrastructureLayerControl({ mapRef, onInfraLayerToggle, infraLayerCounts = {}, isChatExpanded = false, chatPanelHeight = 49, isSidebarCollapsed = false }) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeDbLayers, setActiveDbLayers] = useState(new Set());

  return (
    <div style={{
      position: 'fixed',
      bottom: chatPanelHeight + 16,
      left: (isSidebarCollapsed ? 56 : 140) + 16,
      zIndex: 19,
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      transition: 'left 0.3s ease',
    }}>
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen((v) => !v)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '8px 14px',
          background: isOpen ? '#1a1a1a' : 'rgba(26,26,26,0.9)',
          color: '#e0d6c2',
          border: '1px solid rgba(200,165,92,0.3)',
          borderRadius: 8,
          cursor: 'pointer',
          fontSize: 13,
          fontWeight: 500,
          backdropFilter: 'blur(12px)',
          transition: 'all 0.2s',
          boxShadow: '0 2px 8px rgba(0,0,0,0.3)',
        }}
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <polygon points="12 2 2 7 12 12 22 7" />
          <polyline points="2 17 12 22 22 17" />
          <polyline points="2 12 12 17 22 12" />
        </svg>
        Layers
        {activeDbLayers.size > 0 && (
          <span style={{
            background: '#c8a55c',
            color: '#1a1a1a',
            borderRadius: '50%',
            width: 18,
            height: 18,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 10,
            fontWeight: 700,
          }}>
            {activeDbLayers.size}
          </span>
        )}
      </button>

      {/* Layer Panel */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          bottom: 44,
          left: 0,
          width: 280,
          maxHeight: 420,
          overflowY: 'auto',
          background: 'rgba(26,26,26,0.95)',
          border: '1px solid rgba(200,165,92,0.2)',
          borderRadius: 10,
          padding: '8px 0',
          backdropFilter: 'blur(16px)',
          boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
        }}>
          <div style={{
            padding: '8px 14px 6px',
            fontSize: 11,
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: '#888',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            marginBottom: 4,
          }}>
            Infrastructure
          </div>

          {DB_INFRA_LAYERS.map((layer) => {
            const isActive = activeDbLayers.has(layer.id);
            return (
              <div key={layer.id}
                onClick={() => {
                  const enabled = !isActive;
                  setActiveDbLayers(prev => {
                    const next = new Set(prev);
                    if (enabled) next.add(layer.id); else next.delete(layer.id);
                    return next;
                  });
                  if (onInfraLayerToggle) onInfraLayerToggle(layer.id, enabled);
                }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '6px 14px 6px 20px', cursor: 'pointer',
                  fontSize: 12, color: isActive ? '#e0d6c2' : '#999', transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.04)'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
              >
                <span
                  style={{
                    width: 16, height: 16, borderRadius: 4,
                    border: isActive ? 'none' : '1.5px solid #555',
                    background: isActive ? layer.color : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, transition: 'all 0.15s',
                  }}
                >
                  {isActive && (
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  )}
                </span>
                <span style={{ fontSize: 14, flexShrink: 0 }}>{layer.icon}</span>
                <span style={{ flex: 1 }}>{layer.label}</span>
                {isActive && infraLayerCounts[layer.id] !== undefined && (
                  <span style={{ fontSize: 10, color: infraLayerCounts[layer.id] === 0 ? '#888' : '#c8a55c', fontWeight: 600 }}>
                    {infraLayerCounts[layer.id] === 0 ? 'no data' : `${infraLayerCounts[layer.id]}`}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
