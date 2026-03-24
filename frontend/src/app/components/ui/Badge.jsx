'use client';

const colorMap = {
  gray: { bg: 'rgba(120, 113, 108, 0.15)', text: 'var(--text-muted)', dot: 'var(--text-muted)' },
  blue: { bg: 'rgba(96, 165, 250, 0.15)', text: '#60a5fa', dot: '#60a5fa' },
  amber: { bg: 'rgba(251, 191, 36, 0.15)', text: 'var(--warning)', dot: 'var(--warning)' },
  purple: { bg: 'rgba(167, 139, 250, 0.15)', text: '#a78bfa', dot: '#a78bfa' },
  green: { bg: 'rgba(74, 222, 128, 0.15)', text: 'var(--success)', dot: 'var(--success)' },
  red: { bg: 'rgba(248, 113, 113, 0.15)', text: 'var(--error)', dot: 'var(--error)' },
  gold: { bg: 'var(--accent-bg)', text: 'var(--accent)', dot: 'var(--accent)' },
};

export default function Badge({ color = 'gray', dot, children, style }) {
  const c = colorMap[color] || colorMap.gray;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: '5px',
      padding: '2px 8px', fontSize: 'var(--font-xs)', fontWeight: 'var(--fw-medium)',
      borderRadius: '9999px', background: c.bg, color: c.text,
      lineHeight: 'var(--lh-tight)', whiteSpace: 'nowrap', ...style,
    }}>
      {dot && <span style={{
        width: 6, height: 6, borderRadius: '50%', background: c.dot,
      }} />}
      {children}
    </span>
  );
}
