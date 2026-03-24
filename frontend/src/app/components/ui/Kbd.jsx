'use client';

export default function Kbd({ children, style }) {
  return (
    <kbd style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      padding: '1px 5px', fontSize: 'var(--font-xs)', fontFamily: 'var(--font-family)',
      background: 'var(--bg-tertiary)', color: 'var(--text-muted)',
      borderRadius: '4px', border: '1px solid var(--border)',
      lineHeight: 'var(--lh-tight)', minWidth: 20, ...style,
    }}>
      {children}
    </kbd>
  );
}
