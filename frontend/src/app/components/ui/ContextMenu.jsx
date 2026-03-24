'use client';
import { useState, useRef, useEffect, useCallback } from 'react';

export default function ContextMenu({ items, children }) {
  const [pos, setPos] = useState(null);
  const ref = useRef(null);

  const handleContext = useCallback((e) => {
    e.preventDefault();
    setPos({ x: e.clientX, y: e.clientY });
  }, []);

  useEffect(() => {
    if (!pos) return;
    const handler = () => setPos(null);
    document.addEventListener('click', handler);
    document.addEventListener('contextmenu', handler);
    return () => {
      document.removeEventListener('click', handler);
      document.removeEventListener('contextmenu', handler);
    };
  }, [pos]);

  return (
    <>
      <div onContextMenu={handleContext}>{children}</div>
      {pos && (
        <div ref={ref} style={{
          position: 'fixed', left: pos.x, top: pos.y, zIndex: 9999,
          minWidth: 180, background: 'var(--bg-secondary)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-lg)', padding: '4px',
          animation: 'scaleIn 0.08s var(--ease-enter)',
        }}>
          {items.map((item, i) =>
            item.separator ? (
              <div key={i} style={{ height: 1, background: 'var(--border)', margin: '4px 0' }} />
            ) : (
              <button key={item.id || i} onClick={() => { item.onSelect?.(); setPos(null); }}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '6px 8px', borderRadius: 'var(--radius-sm)',
                  background: 'transparent', color: item.danger ? 'var(--error)' : 'var(--text-primary)',
                  fontSize: 'var(--font-sm)', border: 'none', cursor: 'pointer',
                  fontFamily: 'var(--font-family)', textAlign: 'left',
                  transition: 'background 0.08s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {item.icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{item.icon}</span>}
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.kbd && <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{item.kbd}</span>}
              </button>
            )
          )}
        </div>
      )}
    </>
  );
}
