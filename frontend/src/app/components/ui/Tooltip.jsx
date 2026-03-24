'use client';
import { useState, useRef } from 'react';

export default function Tooltip({ content, side = 'top', delay = 300, children }) {
  const [visible, setVisible] = useState(false);
  const timeout = useRef(null);

  const show = () => { timeout.current = setTimeout(() => setVisible(true), delay); };
  const hide = () => { clearTimeout(timeout.current); setVisible(false); };

  const positions = {
    top: { bottom: '100%', left: '50%', transform: 'translateX(-50%)', marginBottom: 6 },
    bottom: { top: '100%', left: '50%', transform: 'translateX(-50%)', marginTop: 6 },
    left: { right: '100%', top: '50%', transform: 'translateY(-50%)', marginRight: 6 },
    right: { left: '100%', top: '50%', transform: 'translateY(-50%)', marginLeft: 6 },
  };

  return (
    <span style={{ position: 'relative', display: 'inline-flex' }}
      onMouseEnter={show} onMouseLeave={hide} onFocus={show} onBlur={hide}>
      {children}
      {visible && content && (
        <span style={{
          position: 'absolute', ...positions[side],
          padding: '4px 8px', fontSize: 'var(--font-xs)', color: 'var(--text-primary)',
          background: 'var(--bg-tertiary)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)', boxShadow: 'var(--shadow-md)',
          whiteSpace: 'nowrap', pointerEvents: 'none', zIndex: 9999,
          animation: 'scaleIn 0.12s var(--ease-enter)',
        }}>
          {content}
        </span>
      )}
    </span>
  );
}
