'use client';
import { useEffect, useCallback } from 'react';

export default function Modal({ open, onClose, title, children, width = 480, sheet }) {
  const handleEscape = useCallback((e) => {
    if (e.key === 'Escape') onClose?.();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [open, handleEscape]);

  if (!open) return null;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 9990,
      display: 'flex', alignItems: sheet ? 'flex-end' : 'center', justifyContent: 'center',
      background: 'rgba(0, 0, 0, 0.5)', backdropFilter: 'var(--blur)',
      animation: 'backdropIn 0.2s var(--ease-enter)',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: sheet ? '100%' : width, maxWidth: sheet ? '100%' : '90vw',
        maxHeight: sheet ? '85vh' : '80vh',
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: sheet ? 'var(--radius-lg) var(--radius-lg) 0 0' : 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)', overflow: 'hidden',
        animation: sheet ? 'toastSlideIn 0.2s var(--ease-enter)' : 'scaleIn 0.2s var(--ease-enter)',
        display: 'flex', flexDirection: 'column',
      }}>
        {title && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '16px 20px', borderBottom: '1px solid var(--border)',
          }}>
            <h2 style={{
              fontSize: 'var(--font-md)', fontWeight: 'var(--fw-semibold)',
              color: 'var(--text-primary)', margin: 0,
            }}>{title}</h2>
            <button onClick={onClose} style={{
              color: 'var(--text-muted)', fontSize: '18px', cursor: 'pointer',
              background: 'none', border: 'none', padding: 0,
            }}>×</button>
          </div>
        )}
        <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
