'use client';

export default function EmptyState({ icon: Icon, title, description, action, style }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', padding: '48px 24px', textAlign: 'center',
      animation: 'fadeInUp 0.25s var(--ease-enter)', ...style,
    }}>
      {Icon && (
        <div style={{ color: 'var(--text-muted)', marginBottom: 16 }}>
          <Icon size={40} strokeWidth={1.2} />
        </div>
      )}
      {title && (
        <h3 style={{
          fontSize: 'var(--font-md)', fontWeight: 'var(--fw-medium)',
          color: 'var(--text-primary)', marginBottom: 8,
        }}>{title}</h3>
      )}
      {description && (
        <p style={{
          fontSize: 'var(--font-sm)', color: 'var(--text-muted)',
          maxWidth: 280, lineHeight: 'var(--lh-base)',
        }}>{description}</p>
      )}
      {action && <div style={{ marginTop: 16 }}>{action}</div>}
    </div>
  );
}
