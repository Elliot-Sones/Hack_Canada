'use client';
import { useState, useRef, useEffect, useCallback } from 'react';

export default function Dropdown({ trigger, items, groups, searchable, onSelect, align = 'left' }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [focusIndex, setFocusIndex] = useState(-1);
  const ref = useRef(null);
  const inputRef = useRef(null);

  const allItems = groups
    ? groups.flatMap(g => g.items.map(item => ({ ...item, group: g.label })))
    : (items || []);

  const filtered = search
    ? allItems.filter(i => i.label.toLowerCase().includes(search.toLowerCase()))
    : allItems;

  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  useEffect(() => {
    if (open && searchable) inputRef.current?.focus();
    if (!open) { setSearch(''); setFocusIndex(-1); }
  }, [open, searchable]);

  const handleKeyDown = useCallback((e) => {
    if (!open) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setFocusIndex(i => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setFocusIndex(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && focusIndex >= 0) { e.preventDefault(); onSelect?.(filtered[focusIndex]); setOpen(false); }
    if (e.key === 'Escape') setOpen(false);
  }, [open, filtered, focusIndex, onSelect]);

  let lastGroup = null;

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-flex' }} onKeyDown={handleKeyDown}>
      <div onClick={() => setOpen(!open)} style={{ cursor: 'pointer' }}>{trigger}</div>
      {open && (
        <div style={{
          position: 'absolute', top: '100%', [align]: 0, marginTop: 4,
          minWidth: 200, background: 'var(--bg-secondary)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
          animation: 'scaleIn 0.12s var(--ease-enter)', zIndex: 999,
          overflow: 'hidden',
        }}>
          {searchable && (
            <div style={{ padding: '8px' }}>
              <input ref={inputRef} value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search..." style={{
                  width: '100%', padding: '6px 8px', background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)', fontSize: 'var(--font-sm)',
                  outline: 'none', fontFamily: 'var(--font-family)',
                }} />
            </div>
          )}
          <div style={{ maxHeight: 280, overflowY: 'auto', padding: '4px' }}>
            {filtered.map((item, i) => {
              const showGroup = groups && item.group !== lastGroup;
              if (groups) lastGroup = item.group;
              return (
                <div key={item.id || i}>
                  {showGroup && (
                    <div style={{
                      padding: '6px 8px 4px', fontSize: 'var(--font-xs)',
                      color: 'var(--text-muted)', fontWeight: 'var(--fw-medium)',
                    }}>{item.group}</div>
                  )}
                  <button onClick={() => { onSelect?.(item); setOpen(false); }}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '6px 8px', borderRadius: 'var(--radius-sm)',
                      background: i === focusIndex ? 'var(--bg-tertiary)' : 'transparent',
                      color: 'var(--text-primary)', fontSize: 'var(--font-sm)',
                      border: 'none', cursor: 'pointer', fontFamily: 'var(--font-family)',
                      textAlign: 'left', transition: 'background 0.08s',
                    }}
                    onMouseEnter={() => setFocusIndex(i)}
                  >
                    {item.icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{item.icon}</span>}
                    <span style={{ flex: 1 }}>{item.label}</span>
                    {item.kbd && <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{item.kbd}</span>}
                  </button>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: 'var(--font-sm)' }}>No results</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
