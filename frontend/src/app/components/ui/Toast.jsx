'use client';

const typeStyles = {
  info: { borderLeft: '3px solid var(--info)' },
  success: { borderLeft: '3px solid var(--success)' },
  warning: { borderLeft: '3px solid var(--warning)' },
  error: { borderLeft: '3px solid var(--error)' },
};

export default function Toast({ message, type = 'info', undo, onDismiss }) {
  return (
    <div style={{
      pointerEvents: 'auto', display: 'flex', alignItems: 'center', gap: '12px',
      padding: '10px 14px', background: 'var(--bg-secondary)',
      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
      boxShadow: 'var(--shadow-lg)', fontSize: 'var(--font-sm)',
      color: 'var(--text-primary)', animation: 'toastSlideIn 0.15s var(--ease-enter)',
      maxWidth: 380, ...typeStyles[type],
    }}>
      <span style={{ flex: 1 }}>{message}</span>
      {undo && (
        <button onClick={undo} style={{
          color: 'var(--accent)', fontSize: 'var(--font-xs)', fontWeight: 'var(--fw-medium)',
          cursor: 'pointer', background: 'none', border: 'none', fontFamily: 'var(--font-family)',
        }}>Undo</button>
      )}
      <button onClick={onDismiss} style={{
        color: 'var(--text-muted)', cursor: 'pointer', background: 'none',
        border: 'none', fontSize: 'var(--font-sm)', padding: 0, lineHeight: 1,
      }}>×</button>
    </div>
  );
}
