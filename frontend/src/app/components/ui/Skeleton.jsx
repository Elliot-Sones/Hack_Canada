'use client';

export default function Skeleton({ variant = 'line', width, height, style }) {
  const base = {
    background: 'linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-secondary) 50%, var(--bg-tertiary) 75%)',
    backgroundSize: '200% 100%', animation: 'shimmer 1.5s ease-in-out infinite',
    borderRadius: variant === 'circle' ? '50%' : 'var(--radius-sm)',
  };

  const defaults = {
    line: { width: width || '100%', height: height || 14 },
    rect: { width: width || '100%', height: height || 60 },
    circle: { width: width || 32, height: height || 32 },
    card: { width: width || '100%', height: height || 120 },
  };

  return <div style={{ ...base, ...defaults[variant], ...style }} />;
}

export function SkeletonGroup({ lines = 3, gap = 8, style }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap, ...style }}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton key={i} width={i === lines - 1 ? '60%' : '100%'} />
      ))}
    </div>
  );
}
