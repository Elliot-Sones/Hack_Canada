'use client';
import { forwardRef } from 'react';
import Kbd from './Kbd';

const variants = {
  solid: {
    base: { background: 'var(--accent)', color: '#1a1a1a', fontWeight: 'var(--fw-semibold)' },
    hover: { background: 'var(--accent-light)' },
  },
  ghost: {
    base: { background: 'transparent', color: 'var(--text-secondary)' },
    hover: { background: 'var(--bg-tertiary)', color: 'var(--text-primary)' },
  },
  outline: {
    base: { background: 'transparent', color: 'var(--text-primary)', border: '1px solid var(--border)' },
    hover: { borderColor: 'var(--border-accent)', color: 'var(--accent-light)' },
  },
};

const sizes = {
  sm: { padding: '4px 8px', fontSize: 'var(--font-xs)', borderRadius: 'var(--radius-sm)', gap: '4px' },
  md: { padding: '6px 12px', fontSize: 'var(--font-sm)', borderRadius: 'var(--radius-sm)', gap: '6px' },
  lg: { padding: '8px 16px', fontSize: 'var(--font-base)', borderRadius: 'var(--radius-md)', gap: '8px' },
};

const Button = forwardRef(function Button(
  { variant = 'ghost', size = 'md', loading, disabled, kbd, children, style, ...props },
  ref
) {
  const v = variants[variant];
  const s = sizes[size];

  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: s.gap,
        fontFamily: 'var(--font-family)', cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1, transition: 'all 0.15s var(--ease-enter)',
        border: 'none', ...v.base, ...s, ...style,
      }}
      onMouseEnter={e => !disabled && Object.assign(e.currentTarget.style, v.hover)}
      onMouseLeave={e => !disabled && Object.assign(e.currentTarget.style, v.base, s, style)}
      {...props}
    >
      {loading ? (
        <span style={{ width: 14, height: 14, border: '2px solid currentColor',
          borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 0.6s linear infinite',
          display: 'inline-block' }} />
      ) : null}
      {children}
      {kbd ? <Kbd>{kbd}</Kbd> : null}
    </button>
  );
});

export default Button;
