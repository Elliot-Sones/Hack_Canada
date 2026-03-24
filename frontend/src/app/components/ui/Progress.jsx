'use client';

export function ProgressBar({ value = 0, color = 'var(--accent)', style }) {
  return (
    <div style={{
      width: '100%', height: 3, background: 'var(--bg-tertiary)',
      borderRadius: 2, overflow: 'hidden', ...style,
    }}>
      <div style={{
        width: `${Math.min(100, Math.max(0, value))}%`, height: '100%',
        background: color, borderRadius: 2,
        transition: 'width 0.4s var(--ease-enter)',
      }} />
    </div>
  );
}

const stepColors = {
  completed: 'var(--success)',
  active: 'var(--accent)',
  pending: 'var(--text-muted)',
};

export function PipelineStepper({ steps, style }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, ...style }}>
      {steps.map((step, i) => (
        <div key={step.label} style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
            <div style={{
              width: 10, height: 10, borderRadius: '50%',
              background: step.status === 'pending' ? 'transparent' : stepColors[step.status],
              border: `2px solid ${stepColors[step.status]}`,
              animation: step.status === 'active' ? 'statusPulse 2s ease-in-out infinite' : 'none',
            }} />
            <span style={{
              fontSize: 'var(--font-xs)', color: stepColors[step.status],
              fontWeight: step.status === 'active' ? 'var(--fw-semibold)' : 'var(--fw-regular)',
              whiteSpace: 'nowrap',
            }}>{step.label}</span>
          </div>
          {i < steps.length - 1 && (
            <div style={{
              width: 32, height: 2, margin: '0 4px',
              background: step.status === 'completed' ? 'var(--success)' : 'var(--border)',
              marginBottom: 20,
            }} />
          )}
        </div>
      ))}
    </div>
  );
}
