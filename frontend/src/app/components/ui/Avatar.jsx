'use client';

const sizes = { sm: 24, md: 32, lg: 40 };

export default function Avatar({ src, name, size = 'md', status, style }) {
  const s = sizes[size] || sizes.md;
  const initials = name ? name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase() : '?';
  const statusColors = { online: 'var(--success)', away: 'var(--warning)', busy: 'var(--error)' };

  return (
    <div style={{ position: 'relative', width: s, height: s, flexShrink: 0, ...style }}>
      {src ? (
        <img src={src} alt={name || ''} style={{
          width: s, height: s, borderRadius: '50%', objectFit: 'cover',
        }} />
      ) : (
        <div style={{
          width: s, height: s, borderRadius: '50%', background: 'var(--accent-bg)',
          color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: s < 32 ? 'var(--font-xs)' : 'var(--font-sm)', fontWeight: 'var(--fw-semibold)',
        }}>
          {initials}
        </div>
      )}
      {status && statusColors[status] && (
        <span style={{
          position: 'absolute', bottom: 0, right: 0,
          width: s * 0.3, height: s * 0.3, borderRadius: '50%',
          background: statusColors[status], border: '2px solid var(--bg-primary)',
        }} />
      )}
    </div>
  );
}
