'use client';
import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Fuse from 'fuse.js';
import Kbd from './Kbd';

export default function CommandPalette({ open, onClose, actions = [], recentItems = [] }) {
  const [query, setQuery] = useState('');
  const [focusIndex, setFocusIndex] = useState(0);
  const inputRef = useRef(null);

  const fuse = useMemo(() => new Fuse(actions, {
    keys: ['label', 'group'],
    threshold: 0.4,
  }), [actions]);

  const results = query
    ? fuse.search(query).map(r => r.item)
    : recentItems.length > 0
      ? [{ group: 'Recent', items: recentItems }, { group: 'Actions', items: actions }]
          .flatMap(g => g.items.map(i => ({ ...i, _group: g.group })))
      : actions;

  useEffect(() => {
    if (open) { inputRef.current?.focus(); setQuery(''); setFocusIndex(0); }
  }, [open]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setFocusIndex(i => Math.min(i + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setFocusIndex(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && results[focusIndex]) { results[focusIndex].onSelect?.(); onClose(); }
    if (e.key === 'Escape') onClose();
  }, [results, focusIndex, onClose]);

  if (!open) return null;

  let lastGroup = null;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      paddingTop: '20vh', background: 'rgba(0, 0, 0, 0.5)',
      backdropFilter: 'var(--blur)',
      animation: 'backdropIn 0.2s var(--ease-enter)',
    }}>
      <div onClick={e => e.stopPropagation()} onKeyDown={handleKeyDown}
        style={{
          width: 520, maxHeight: '50vh', background: 'var(--bg-secondary)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)', overflow: 'hidden',
          animation: 'scaleIn 0.15s var(--ease-enter)',
          display: 'flex', flexDirection: 'column',
        }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '12px 16px', borderBottom: '1px solid var(--border)',
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <input ref={inputRef} value={query} onChange={e => { setQuery(e.target.value); setFocusIndex(0); }}
            placeholder="Search parcels, actions, views..."
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: 'var(--text-primary)', fontSize: 'var(--font-base)',
              fontFamily: 'var(--font-family)',
            }} />
          <Kbd>Esc</Kbd>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '4px' }}>
          {results.map((item, i) => {
            const showGroup = item._group && item._group !== lastGroup;
            if (item._group) lastGroup = item._group;
            return (
              <div key={item.id || i}>
                {showGroup && (
                  <div style={{
                    padding: '8px 12px 4px', fontSize: 'var(--font-xs)',
                    color: 'var(--text-muted)', fontWeight: 'var(--fw-medium)',
                    textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>{item._group}</div>
                )}
                <button onClick={() => { item.onSelect?.(); onClose(); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '8px 12px', borderRadius: 'var(--radius-sm)',
                    background: i === focusIndex ? 'var(--bg-tertiary)' : 'transparent',
                    color: 'var(--text-primary)', fontSize: 'var(--font-sm)',
                    border: 'none', cursor: 'pointer', fontFamily: 'var(--font-family)',
                    textAlign: 'left', transition: 'background 0.08s',
                  }}
                  onMouseEnter={() => setFocusIndex(i)}
                >
                  {item.icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{item.icon}</span>}
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.kbd && <Kbd>{item.kbd}</Kbd>}
                </button>
              </div>
            );
          })}
          {results.length === 0 && (
            <div style={{
              padding: '24px', textAlign: 'center',
              color: 'var(--text-muted)', fontSize: 'var(--font-sm)',
            }}>No results for &ldquo;{query}&rdquo;</div>
          )}
        </div>
      </div>
    </div>
  );
}
