'use client';
import { useRef, useState, useEffect } from 'react';

export default function Tabs({ tabs, active, onChange, style }) {
  const containerRef = useRef(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    const activeEl = containerRef.current.querySelector(`[data-tab="${active}"]`);
    if (activeEl) {
      const containerRect = containerRef.current.getBoundingClientRect();
      const tabRect = activeEl.getBoundingClientRect();
      setIndicator({
        left: tabRect.left - containerRect.left,
        width: tabRect.width,
      });
    }
  }, [active]);

  return (
    <div ref={containerRef} style={{
      display: 'flex', gap: 0, position: 'relative',
      borderBottom: '1px solid var(--border)', ...style,
    }}>
      {tabs.map(tab => (
        <button key={tab.id} data-tab={tab.id}
          onClick={() => onChange(tab.id)}
          style={{
            padding: '8px 14px', fontSize: 'var(--font-sm)',
            fontWeight: active === tab.id ? 'var(--fw-medium)' : 'var(--fw-regular)',
            color: active === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
            background: 'none', border: 'none', cursor: 'pointer',
            fontFamily: 'var(--font-family)', transition: 'color 0.15s',
            position: 'relative',
          }}
        >
          {tab.label}
          {tab.count != null && (
            <span style={{ marginLeft: 6, fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{tab.count}</span>
          )}
        </button>
      ))}
      <div style={{
        position: 'absolute', bottom: -1, height: 2,
        background: 'var(--accent)', borderRadius: 1,
        left: indicator.left, width: indicator.width,
        transition: 'left 0.3s var(--ease-spring), width 0.3s var(--ease-spring)',
      }} />
    </div>
  );
}
