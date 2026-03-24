'use client';
import { forwardRef } from 'react';

const Input = forwardRef(function Input(
  { icon, suffix, error, style, containerStyle, ...props },
  ref
) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: '8px',
      padding: '6px 12px', background: 'var(--bg-secondary)',
      border: `1px solid ${error ? 'var(--error)' : 'var(--border)'}`,
      borderRadius: 'var(--radius-sm)', transition: 'border-color 0.15s var(--ease-enter)',
      ...containerStyle,
    }}
    onFocus={e => { if (!error) e.currentTarget.style.borderColor = 'var(--accent)'; }}
    onBlur={e => { e.currentTarget.style.borderColor = error ? 'var(--error)' : 'var(--border)'; }}
    >
      {icon && <span style={{ color: 'var(--text-muted)', display: 'flex', flexShrink: 0 }}>{icon}</span>}
      <input
        ref={ref}
        style={{
          flex: 1, background: 'none', border: 'none', outline: 'none',
          color: 'var(--text-primary)', fontSize: 'var(--font-base)',
          fontFamily: 'var(--font-family)', lineHeight: 'var(--lh-base)',
          ...style,
        }}
        {...props}
      />
      {suffix && <span style={{ color: 'var(--text-muted)', display: 'flex', flexShrink: 0 }}>{suffix}</span>}
    </div>
  );
});

export default Input;
