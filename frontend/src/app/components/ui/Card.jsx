'use client';

export default function Card({ children, onClick, hover = true, style }) {
  return (
    <div onClick={onClick} style={{
      padding: '14px 16px', background: 'var(--bg-secondary)',
      border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
      cursor: onClick ? 'pointer' : 'default',
      transition: 'all 0.12s var(--ease-enter)', ...style,
    }}
    onMouseEnter={e => {
      if (!hover) return;
      e.currentTarget.style.borderColor = 'var(--border-accent)';
      e.currentTarget.style.transform = 'translateY(-1px)';
      e.currentTarget.style.boxShadow = 'var(--shadow-md)';
    }}
    onMouseLeave={e => {
      if (!hover) return;
      e.currentTarget.style.borderColor = 'var(--border)';
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      {children}
    </div>
  );
}
