# Linear UI Overhaul — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform CoCivil's dashboard into a Linear-quality UI with a component library, restructured navigation, status pipeline, micro-interactions, and polished empty states.

**Architecture:** Build 15 reusable UI primitives in `components/ui/`, then restructure the dashboard layout (top bar + sidebar + main + detail panel), relocate chat to a detail panel tab, add parcel status pipeline, command palette, toast system, and keyboard shortcuts. All changes are client-side React components using existing CSS variables.

**Tech Stack:** React 19, Next.js 16, CSS Variables, Lucide React icons, fuse.js (fuzzy search)

**Spec:** `docs/superpowers/specs/2026-03-23-linear-ui-overhaul-design.md`

---

## File Structure

### New Files (components/ui/)
```
frontend/src/app/components/ui/
  Button.jsx          — Ghost/solid/outline button with loading + kbd hint
  Input.jsx           — Styled input with icon slots, error state
  Badge.jsx           — Status dot/pill badges with color variants
  Tooltip.jsx         — Hover tooltip with delay and positioning
  Dropdown.jsx        — Keyboard-navigable dropdown with search
  Modal.jsx           — Backdrop blur modal + sheet variant
  CommandPalette.jsx  — Cmd+K fuzzy search across parcels/actions
  Toast.jsx           — Individual toast component
  ToastProvider.jsx   — Toast context + stacking manager
  Skeleton.jsx        — Shimmer loader (line/rect/card variants)
  Tabs.jsx            — Animated underline tab bar
  Kbd.jsx             — Keyboard shortcut display chip
  Progress.jsx        — Horizontal bar + pipeline stepper
  Avatar.jsx          — Image/initials with status dot
  Card.jsx            — Hover-lift card with border highlight
  ContextMenu.jsx     — Right-click menu with kbd hints
  EmptyState.jsx      — Centered empty view with icon + CTA
```

### New Files (other)
```
frontend/src/app/components/TopBar.jsx       — Logo + command palette trigger + avatar
frontend/src/app/components/DetailPanel.jsx  — Right panel with tab switching (Policy/Zoning/Infra/Chat/Docs)
frontend/src/app/hooks/useKeyboardShortcuts.js — Global keyboard shortcut manager
frontend/src/app/hooks/useToast.js           — Toast hook (re-exports from ToastProvider)
frontend/src/app/styles/spacing.css          — 4px grid spacing utilities
```

### Modified Files
```
frontend/src/app/styles/variables.css        — Tighten typography, update sidebar width, add new tokens
frontend/src/app/styles/animations.css       — Add new keyframes (shimmer, slideUp, scaleIn, fadeInUp)
frontend/src/app/styles/index.css            — Import spacing.css
frontend/src/app/styles/sidebar.css          — Linear-style workspace nav
frontend/src/app/styles/panel.css            — Detail panel tabs + layout
frontend/src/app/styles/chat.css             — Chat as detail panel tab (not bottom bar)
frontend/src/app/components/DashboardView.jsx — New layout: TopBar + Sidebar + Main + DetailPanel
frontend/src/app/components/Sidebar.jsx      — Workspace groups (Parcels/Projects/Views), status icons
frontend/src/app/components/ChatPanel.jsx    — Adapt to render inside DetailPanel tab
frontend/src/app/components/PolicyPanel.jsx  — Content becomes tabs inside DetailPanel
frontend/src/app/components/SearchBar.jsx    — Integrate with CommandPalette
frontend/src/app/components/MapView.jsx      — Full height (no bottom chat)
```

---

## Task 1: Design Token Updates

**Files:**
- Modify: `frontend/src/app/styles/variables.css`
- Create: `frontend/src/app/styles/spacing.css`
- Modify: `frontend/src/app/styles/index.css`

- [ ] **Step 1: Update variables.css typography tokens**

In `variables.css`, replace lines 31–36 (typography) with tightened Linear-density values:

```css
/* Typography — Linear density */
--font-xs: 0.6875rem;    /* 11px */
--font-sm: 0.75rem;      /* 12px */
--font-base: 0.8125rem;  /* 13px */
--font-md: 0.875rem;     /* 14px */
--font-lg: 1rem;         /* 16px */
--font-xl: 1.25rem;      /* 20px */

/* Line heights */
--lh-tight: 1rem;        /* 16px — xs, sm */
--lh-base: 1.25rem;      /* 20px — base, md */
--lh-loose: 1.5rem;      /* 24px — lg */
--lh-xl: 1.75rem;        /* 28px — xl */

/* Font weights */
--fw-regular: 400;
--fw-medium: 500;
--fw-semibold: 600;
```

- [ ] **Step 2: Update sidebar width in variables.css**

Change `--sidebar-width: 160px` → `--sidebar-width: 220px` on line 47. Keep `--sidebar-collapsed: 52px`.

- [ ] **Step 3: Add status colors to variables.css**

After line 27 (`--error`), add:

```css
--info: #60a5fa;
--purple: #a78bfa;
```

- [ ] **Step 4: Add easing tokens to variables.css**

After line 62 (`--transition`), add:

```css
--ease-enter: cubic-bezier(0, 0, 0.2, 1);
--ease-exit: cubic-bezier(0.4, 0, 1, 1);
--ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
```

- [ ] **Step 5: Create spacing.css**

```css
/* 4px grid spacing utilities */
.gap-1 { gap: var(--space-xs); }
.gap-2 { gap: var(--space-sm); }
.gap-3 { gap: var(--space-md); }
.gap-4 { gap: var(--space-lg); }
.gap-6 { gap: var(--space-xl); }
.gap-8 { gap: var(--space-2xl); }

.p-1 { padding: var(--space-xs); }
.p-2 { padding: var(--space-sm); }
.p-3 { padding: var(--space-md); }
.p-4 { padding: var(--space-lg); }

.px-2 { padding-left: var(--space-sm); padding-right: var(--space-sm); }
.px-3 { padding-left: var(--space-md); padding-right: var(--space-md); }
.px-4 { padding-left: var(--space-lg); padding-right: var(--space-lg); }

.py-1 { padding-top: var(--space-xs); padding-bottom: var(--space-xs); }
.py-2 { padding-top: var(--space-sm); padding-bottom: var(--space-sm); }
.py-3 { padding-top: var(--space-md); padding-bottom: var(--space-md); }

.mt-2 { margin-top: var(--space-sm); }
.mt-4 { margin-top: var(--space-lg); }
.mb-2 { margin-bottom: var(--space-sm); }
.mb-4 { margin-bottom: var(--space-lg); }
```

- [ ] **Step 6: Add spacing.css import to index.css**

Add `@import './spacing.css';` after `variables.css` import (line 13 of index.css).

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/styles/variables.css frontend/src/app/styles/spacing.css frontend/src/app/styles/index.css
git commit -m "chore: tighten typography, add spacing utilities, update design tokens"
```

---

## Task 2: Animation Keyframes

**Files:**
- Modify: `frontend/src/app/styles/animations.css`

- [ ] **Step 1: Add new keyframes to animations.css**

Append after the existing keyframes (after line 183):

```css
/* ── Linear-style micro-interactions ── */

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes toastSlideIn {
  from { transform: translateY(16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes toastFadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

@keyframes backdropIn {
  from { backdrop-filter: blur(0); background: transparent; }
  to { backdrop-filter: var(--blur); background: rgba(0, 0, 0, 0.5); }
}

@keyframes statusPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

@keyframes underlineSlide {
  from { transform: translateX(var(--tab-from)); width: var(--tab-from-width); }
  to { transform: translateX(var(--tab-to)); width: var(--tab-to-width); }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/styles/animations.css
git commit -m "feat: add shimmer, toast, scale, backdrop, status pulse keyframes"
```

---

## Task 3: Core UI Primitives (Button, Input, Badge, Kbd, Avatar)

**Files:**
- Create: `frontend/src/app/components/ui/Button.jsx`
- Create: `frontend/src/app/components/ui/Input.jsx`
- Create: `frontend/src/app/components/ui/Badge.jsx`
- Create: `frontend/src/app/components/ui/Kbd.jsx`
- Create: `frontend/src/app/components/ui/Avatar.jsx`

- [ ] **Step 1: Create Button.jsx**

```jsx
'use client';
import { forwardRef } from 'react';

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

function Kbd({ children }) {
  return (
    <kbd style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      padding: '1px 5px', fontSize: 'var(--font-xs)', fontFamily: 'var(--font-family)',
      background: 'var(--bg-tertiary)', color: 'var(--text-muted)',
      borderRadius: '4px', border: '1px solid var(--border)',
      lineHeight: 'var(--lh-tight)', minWidth: 20,
    }}>
      {children}
    </kbd>
  );
}

export default Button;
export { Kbd };
```

- [ ] **Step 2: Create Input.jsx**

```jsx
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
```

- [ ] **Step 3: Create Badge.jsx**

```jsx
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
```

- [ ] **Step 4: Create Kbd.jsx** (standalone export)

```jsx
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
```

- [ ] **Step 5: Create Avatar.jsx**

```jsx
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
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/components/ui/
git commit -m "feat: add core UI primitives — Button, Input, Badge, Kbd, Avatar"
```

---

## Task 4: Feedback Primitives (Toast, Skeleton, Progress, EmptyState)

**Files:**
- Create: `frontend/src/app/components/ui/ToastProvider.jsx`
- Create: `frontend/src/app/components/ui/Toast.jsx`
- Create: `frontend/src/app/hooks/useToast.js`
- Create: `frontend/src/app/components/ui/Skeleton.jsx`
- Create: `frontend/src/app/components/ui/Progress.jsx`
- Create: `frontend/src/app/components/ui/EmptyState.jsx`

- [ ] **Step 1: Create ToastProvider.jsx**

```jsx
'use client';
import { createContext, useCallback, useState } from 'react';
import Toast from './Toast';

export const ToastContext = createContext(null);

let toastId = 0;

export default function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback(({ message, type = 'info', duration = 4000, undo }) => {
    const id = ++toastId;
    setToasts(prev => [...prev, { id, message, type, undo }]);
    if (duration > 0) {
      setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), duration);
    }
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div style={{
        position: 'fixed', bottom: 16, left: 16, zIndex: 9999,
        display: 'flex', flexDirection: 'column', gap: '8px',
        pointerEvents: 'none',
      }}>
        {toasts.map(t => (
          <Toast key={t.id} {...t} onDismiss={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
```

- [ ] **Step 2: Create Toast.jsx**

```jsx
'use client';

const typeStyles = {
  info: { borderLeft: '3px solid var(--info)' },
  success: { borderLeft: '3px solid var(--success)' },
  warning: { borderLeft: '3px solid var(--warning)' },
  error: { borderLeft: '3px solid var(--error)' },
};

export default function Toast({ message, type = 'info', undo, onDismiss }) {
  return (
    <div style={{
      pointerEvents: 'auto', display: 'flex', alignItems: 'center', gap: '12px',
      padding: '10px 14px', background: 'var(--bg-secondary)',
      border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
      boxShadow: 'var(--shadow-lg)', fontSize: 'var(--font-sm)',
      color: 'var(--text-primary)', animation: 'toastSlideIn 0.15s var(--ease-enter)',
      maxWidth: 380, ...typeStyles[type],
    }}>
      <span style={{ flex: 1 }}>{message}</span>
      {undo && (
        <button onClick={undo} style={{
          color: 'var(--accent)', fontSize: 'var(--font-xs)', fontWeight: 'var(--fw-medium)',
          cursor: 'pointer', background: 'none', border: 'none', fontFamily: 'var(--font-family)',
        }}>Undo</button>
      )}
      <button onClick={onDismiss} style={{
        color: 'var(--text-muted)', cursor: 'pointer', background: 'none',
        border: 'none', fontSize: 'var(--font-sm)', padding: 0, lineHeight: 1,
      }}>×</button>
    </div>
  );
}
```

- [ ] **Step 3: Create useToast.js**

```js
import { useContext } from 'react';
import { ToastContext } from '../components/ui/ToastProvider';

export default function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within ToastProvider');
  return ctx;
}
```

- [ ] **Step 4: Create Skeleton.jsx**

```jsx
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
```

- [ ] **Step 5: Create Progress.jsx**

```jsx
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
```

- [ ] **Step 6: Create EmptyState.jsx**

```jsx
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
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/components/ui/ToastProvider.jsx frontend/src/app/components/ui/Toast.jsx frontend/src/app/hooks/useToast.js frontend/src/app/components/ui/Skeleton.jsx frontend/src/app/components/ui/Progress.jsx frontend/src/app/components/ui/EmptyState.jsx
git commit -m "feat: add feedback primitives — Toast, Skeleton, Progress, EmptyState"
```

---

## Task 5: Overlay Primitives (Tooltip, Dropdown, Modal, Tabs, Card, ContextMenu)

**Files:**
- Create: `frontend/src/app/components/ui/Tooltip.jsx`
- Create: `frontend/src/app/components/ui/Dropdown.jsx`
- Create: `frontend/src/app/components/ui/Modal.jsx`
- Create: `frontend/src/app/components/ui/Tabs.jsx`
- Create: `frontend/src/app/components/ui/Card.jsx`
- Create: `frontend/src/app/components/ui/ContextMenu.jsx`

- [ ] **Step 1: Create Tooltip.jsx**

```jsx
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
```

- [ ] **Step 2: Create Dropdown.jsx**

```jsx
'use client';
import { useState, useRef, useEffect, useCallback } from 'react';

export default function Dropdown({ trigger, items, groups, searchable, onSelect, align = 'left' }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');
  const [focusIndex, setFocusIndex] = useState(-1);
  const ref = useRef(null);
  const inputRef = useRef(null);

  const allItems = groups
    ? groups.flatMap(g => g.items.map(item => ({ ...item, group: g.label })))
    : (items || []);

  const filtered = search
    ? allItems.filter(i => i.label.toLowerCase().includes(search.toLowerCase()))
    : allItems;

  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  useEffect(() => {
    if (open && searchable) inputRef.current?.focus();
    if (!open) { setSearch(''); setFocusIndex(-1); }
  }, [open, searchable]);

  const handleKeyDown = useCallback((e) => {
    if (!open) return;
    if (e.key === 'ArrowDown') { e.preventDefault(); setFocusIndex(i => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setFocusIndex(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && focusIndex >= 0) { e.preventDefault(); onSelect?.(filtered[focusIndex]); setOpen(false); }
    if (e.key === 'Escape') setOpen(false);
  }, [open, filtered, focusIndex, onSelect]);

  let lastGroup = null;

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-flex' }} onKeyDown={handleKeyDown}>
      <div onClick={() => setOpen(!open)} style={{ cursor: 'pointer' }}>{trigger}</div>
      {open && (
        <div style={{
          position: 'absolute', top: '100%', [align]: 0, marginTop: 4,
          minWidth: 200, background: 'var(--bg-secondary)', border: '1px solid var(--border)',
          borderRadius: 'var(--radius-md)', boxShadow: 'var(--shadow-lg)',
          animation: 'scaleIn 0.12s var(--ease-enter)', zIndex: 999,
          overflow: 'hidden',
        }}>
          {searchable && (
            <div style={{ padding: '8px' }}>
              <input ref={inputRef} value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Search..." style={{
                  width: '100%', padding: '6px 8px', background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
                  color: 'var(--text-primary)', fontSize: 'var(--font-sm)',
                  outline: 'none', fontFamily: 'var(--font-family)',
                }} />
            </div>
          )}
          <div style={{ maxHeight: 280, overflowY: 'auto', padding: '4px' }}>
            {filtered.map((item, i) => {
              const showGroup = groups && item.group !== lastGroup;
              lastGroup = item.group;
              return (
                <div key={item.id || i}>
                  {showGroup && (
                    <div style={{
                      padding: '6px 8px 4px', fontSize: 'var(--font-xs)',
                      color: 'var(--text-muted)', fontWeight: 'var(--fw-medium)',
                    }}>{item.group}</div>
                  )}
                  <button onClick={() => { onSelect?.(item); setOpen(false); }}
                    style={{
                      width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
                      padding: '6px 8px', borderRadius: 'var(--radius-sm)',
                      background: i === focusIndex ? 'var(--bg-tertiary)' : 'transparent',
                      color: 'var(--text-primary)', fontSize: 'var(--font-sm)',
                      border: 'none', cursor: 'pointer', fontFamily: 'var(--font-family)',
                      textAlign: 'left', transition: 'background 0.08s',
                    }}
                    onMouseEnter={() => setFocusIndex(i)}
                  >
                    {item.icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{item.icon}</span>}
                    <span style={{ flex: 1 }}>{item.label}</span>
                    {item.kbd && <span style={{
                      fontSize: 'var(--font-xs)', color: 'var(--text-muted)',
                    }}>{item.kbd}</span>}
                  </button>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div style={{
                padding: '16px', textAlign: 'center',
                color: 'var(--text-muted)', fontSize: 'var(--font-sm)',
              }}>No results</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create Modal.jsx**

```jsx
'use client';
import { useEffect, useCallback } from 'react';

export default function Modal({ open, onClose, title, children, width = 480, sheet }) {
  const handleEscape = useCallback((e) => {
    if (e.key === 'Escape') onClose?.();
  }, [onClose]);

  useEffect(() => {
    if (!open) return;
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [open, handleEscape]);

  if (!open) return null;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 9990,
      display: 'flex', alignItems: sheet ? 'flex-end' : 'center', justifyContent: 'center',
      background: 'rgba(0, 0, 0, 0.5)', backdropFilter: 'var(--blur)',
      animation: 'backdropIn 0.2s var(--ease-enter)',
    }}>
      <div onClick={e => e.stopPropagation()} style={{
        width: sheet ? '100%' : width, maxWidth: sheet ? '100%' : '90vw',
        maxHeight: sheet ? '85vh' : '80vh',
        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
        borderRadius: sheet ? 'var(--radius-lg) var(--radius-lg) 0 0' : 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)', overflow: 'hidden',
        animation: sheet ? 'toastSlideIn 0.2s var(--ease-enter)' : 'scaleIn 0.2s var(--ease-enter)',
        display: 'flex', flexDirection: 'column',
      }}>
        {title && (
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            padding: '16px 20px', borderBottom: '1px solid var(--border)',
          }}>
            <h2 style={{
              fontSize: 'var(--font-md)', fontWeight: 'var(--fw-semibold)',
              color: 'var(--text-primary)', margin: 0,
            }}>{title}</h2>
            <button onClick={onClose} style={{
              color: 'var(--text-muted)', fontSize: '18px', cursor: 'pointer',
              background: 'none', border: 'none', padding: 0,
            }}>×</button>
          </div>
        )}
        <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
          {children}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Create Tabs.jsx**

```jsx
'use client';
import { useRef, useState, useEffect } from 'react';

export default function Tabs({ tabs, active, onChange, style }) {
  const containerRef = useRef(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0 });

  useEffect(() => {
    if (!containerRef.current) return;
    const activeEl = containerRef.current.querySelector(`[data-tab="${active}"]`);
    if (activeEl) {
      const containerRect = containerRef.current.getBoundingClientRect();
      const tabRect = activeEl.getBoundingClientRect();
      setIndicator({
        left: tabRect.left - containerRect.left,
        width: tabRect.width,
      });
    }
  }, [active]);

  return (
    <div ref={containerRef} style={{
      display: 'flex', gap: 0, position: 'relative',
      borderBottom: '1px solid var(--border)', ...style,
    }}>
      {tabs.map(tab => (
        <button key={tab.id} data-tab={tab.id}
          onClick={() => onChange(tab.id)}
          style={{
            padding: '8px 14px', fontSize: 'var(--font-sm)',
            fontWeight: active === tab.id ? 'var(--fw-medium)' : 'var(--fw-regular)',
            color: active === tab.id ? 'var(--text-primary)' : 'var(--text-muted)',
            background: 'none', border: 'none', cursor: 'pointer',
            fontFamily: 'var(--font-family)', transition: 'color 0.15s',
            position: 'relative',
          }}
        >
          {tab.label}
          {tab.count != null && (
            <span style={{
              marginLeft: 6, fontSize: 'var(--font-xs)', color: 'var(--text-muted)',
            }}>{tab.count}</span>
          )}
        </button>
      ))}
      <div style={{
        position: 'absolute', bottom: -1, height: 2,
        background: 'var(--accent)', borderRadius: 1,
        left: indicator.left, width: indicator.width,
        transition: 'left 0.3s var(--ease-spring), width 0.3s var(--ease-spring)',
      }} />
    </div>
  );
}
```

- [ ] **Step 5: Create Card.jsx**

```jsx
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
```

- [ ] **Step 6: Create ContextMenu.jsx**

```jsx
'use client';
import { useState, useRef, useEffect, useCallback } from 'react';

export default function ContextMenu({ items, children }) {
  const [pos, setPos] = useState(null);
  const ref = useRef(null);

  const handleContext = useCallback((e) => {
    e.preventDefault();
    setPos({ x: e.clientX, y: e.clientY });
  }, []);

  useEffect(() => {
    if (!pos) return;
    const handler = () => setPos(null);
    document.addEventListener('click', handler);
    document.addEventListener('contextmenu', handler);
    return () => {
      document.removeEventListener('click', handler);
      document.removeEventListener('contextmenu', handler);
    };
  }, [pos]);

  return (
    <>
      <div onContextMenu={handleContext}>{children}</div>
      {pos && (
        <div ref={ref} style={{
          position: 'fixed', left: pos.x, top: pos.y, zIndex: 9999,
          minWidth: 180, background: 'var(--bg-secondary)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
          boxShadow: 'var(--shadow-lg)', padding: '4px',
          animation: 'scaleIn 0.08s var(--ease-enter)',
        }}>
          {items.map((item, i) =>
            item.separator ? (
              <div key={i} style={{ height: 1, background: 'var(--border)', margin: '4px 0' }} />
            ) : (
              <button key={item.id || i} onClick={() => { item.onSelect?.(); setPos(null); }}
                style={{
                  width: '100%', display: 'flex', alignItems: 'center', gap: '8px',
                  padding: '6px 8px', borderRadius: 'var(--radius-sm)',
                  background: 'transparent', color: item.danger ? 'var(--error)' : 'var(--text-primary)',
                  fontSize: 'var(--font-sm)', border: 'none', cursor: 'pointer',
                  fontFamily: 'var(--font-family)', textAlign: 'left',
                  transition: 'background 0.08s',
                }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-tertiary)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                {item.icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{item.icon}</span>}
                <span style={{ flex: 1 }}>{item.label}</span>
                {item.kbd && <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>{item.kbd}</span>}
              </button>
            )
          )}
        </div>
      )}
    </>
  );
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/components/ui/
git commit -m "feat: add overlay primitives — Tooltip, Dropdown, Modal, Tabs, Card, ContextMenu"
```

---

## Task 6: Command Palette

**Files:**
- Create: `frontend/src/app/components/ui/CommandPalette.jsx`
- Install: `fuse.js`

- [ ] **Step 1: Install fuse.js**

```bash
cd frontend && npm install fuse.js
```

- [ ] **Step 2: Create CommandPalette.jsx**

```jsx
'use client';
import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Fuse from 'fuse.js';
import Kbd from './Kbd';

export default function CommandPalette({ open, onClose, actions = [], recentItems = [] }) {
  const [query, setQuery] = useState('');
  const [focusIndex, setFocusIndex] = useState(0);
  const inputRef = useRef(null);

  const fuse = useMemo(() => new Fuse(actions, {
    keys: ['label', 'group'],
    threshold: 0.4,
  }), [actions]);

  const results = query
    ? fuse.search(query).map(r => r.item)
    : recentItems.length > 0
      ? [{ group: 'Recent', items: recentItems }, { group: 'Actions', items: actions }]
          .flatMap(g => g.items.map(i => ({ ...i, _group: g.group })))
      : actions;

  useEffect(() => {
    if (open) { inputRef.current?.focus(); setQuery(''); setFocusIndex(0); }
  }, [open]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setFocusIndex(i => Math.min(i + 1, results.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setFocusIndex(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && results[focusIndex]) { results[focusIndex].onSelect?.(); onClose(); }
    if (e.key === 'Escape') onClose();
  }, [results, focusIndex, onClose]);

  if (!open) return null;

  let lastGroup = null;

  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, zIndex: 9999,
      display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
      paddingTop: '20vh', background: 'rgba(0, 0, 0, 0.5)',
      backdropFilter: 'var(--blur)',
      animation: 'backdropIn 0.2s var(--ease-enter)',
    }}>
      <div onClick={e => e.stopPropagation()} onKeyDown={handleKeyDown}
        style={{
          width: 520, maxHeight: '50vh', background: 'var(--bg-secondary)',
          border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)', overflow: 'hidden',
          animation: 'scaleIn 0.15s var(--ease-enter)',
          display: 'flex', flexDirection: 'column',
        }}>
        <div style={{
          display: 'flex', alignItems: 'center', gap: '8px',
          padding: '12px 16px', borderBottom: '1px solid var(--border)',
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
          <input ref={inputRef} value={query} onChange={e => { setQuery(e.target.value); setFocusIndex(0); }}
            placeholder="Search parcels, actions, views..."
            style={{
              flex: 1, background: 'none', border: 'none', outline: 'none',
              color: 'var(--text-primary)', fontSize: 'var(--font-base)',
              fontFamily: 'var(--font-family)',
            }} />
          <Kbd>Esc</Kbd>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '4px' }}>
          {results.map((item, i) => {
            const showGroup = item._group && item._group !== lastGroup;
            lastGroup = item._group;
            return (
              <div key={item.id || i}>
                {showGroup && (
                  <div style={{
                    padding: '8px 12px 4px', fontSize: 'var(--font-xs)',
                    color: 'var(--text-muted)', fontWeight: 'var(--fw-medium)',
                    textTransform: 'uppercase', letterSpacing: '0.05em',
                  }}>{item._group}</div>
                )}
                <button onClick={() => { item.onSelect?.(); onClose(); }}
                  style={{
                    width: '100%', display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '8px 12px', borderRadius: 'var(--radius-sm)',
                    background: i === focusIndex ? 'var(--bg-tertiary)' : 'transparent',
                    color: 'var(--text-primary)', fontSize: 'var(--font-sm)',
                    border: 'none', cursor: 'pointer', fontFamily: 'var(--font-family)',
                    textAlign: 'left', transition: 'background 0.08s',
                  }}
                  onMouseEnter={() => setFocusIndex(i)}
                >
                  {item.icon && <span style={{ color: 'var(--text-muted)', display: 'flex' }}>{item.icon}</span>}
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.kbd && <Kbd>{item.kbd}</Kbd>}
                </button>
              </div>
            );
          })}
          {results.length === 0 && (
            <div style={{
              padding: '24px', textAlign: 'center',
              color: 'var(--text-muted)', fontSize: 'var(--font-sm)',
            }}>No results for "{query}"</div>
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/components/ui/CommandPalette.jsx frontend/package.json frontend/package-lock.json
git commit -m "feat: add command palette with fuse.js fuzzy search"
```

---

## Task 7: Keyboard Shortcuts Hook

**Files:**
- Create: `frontend/src/app/hooks/useKeyboardShortcuts.js`

- [ ] **Step 1: Create useKeyboardShortcuts.js**

```js
'use client';
import { useEffect, useCallback } from 'react';

export default function useKeyboardShortcuts(shortcuts) {
  const handler = useCallback((e) => {
    // Don't fire when typing in inputs (unless shortcut uses meta/ctrl)
    const isInput = ['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName);
    const hasMeta = e.metaKey || e.ctrlKey;

    for (const s of shortcuts) {
      const keyMatch = e.key.toLowerCase() === s.key.toLowerCase();
      const metaMatch = s.meta ? hasMeta : !hasMeta;
      const shiftMatch = s.shift ? e.shiftKey : true;

      if (keyMatch && metaMatch && shiftMatch) {
        if (isInput && !hasMeta) continue; // skip if in input without meta
        e.preventDefault();
        s.action();
        return;
      }
    }
  }, [shortcuts]);

  useEffect(() => {
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [handler]);
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/hooks/useKeyboardShortcuts.js
git commit -m "feat: add global keyboard shortcuts hook"
```

---

## Task 8: TopBar Component

**Files:**
- Create: `frontend/src/app/components/TopBar.jsx`

- [ ] **Step 1: Create TopBar.jsx**

```jsx
'use client';
import { Search } from 'lucide-react';
import Avatar from './ui/Avatar';
import Kbd from './ui/Kbd';
import Dropdown from './ui/Dropdown';

export default function TopBar({ user, onCommandPalette, onSignOut, onSettings }) {
  return (
    <header style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      height: 48, padding: '0 16px',
      background: 'var(--bg-primary)', borderBottom: '1px solid var(--border)',
      zIndex: 100, flexShrink: 0,
    }}>
      {/* Left: Logo */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        fontSize: 'var(--font-md)', fontWeight: 'var(--fw-semibold)',
        color: 'var(--accent)',
      }}>
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
        CoCivil
      </div>

      {/* Center: Command palette trigger */}
      <button onClick={onCommandPalette} style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        padding: '6px 14px', background: 'var(--bg-secondary)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
        color: 'var(--text-muted)', fontSize: 'var(--font-sm)',
        cursor: 'pointer', fontFamily: 'var(--font-family)',
        transition: 'border-color 0.15s',
        minWidth: 280,
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-accent)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
      >
        <Search size={14} />
        <span style={{ flex: 1, textAlign: 'left' }}>Search or jump to...</span>
        <Kbd>⌘K</Kbd>
      </button>

      {/* Right: User */}
      <Dropdown
        align="right"
        trigger={
          <Avatar name={user?.name || user?.email} src={user?.image} size="sm" />
        }
        items={[
          { id: 'settings', label: 'Settings', kbd: '⌘,', onSelect: onSettings },
          { id: 'signout', label: 'Sign out', onSelect: onSignOut },
        ]}
        onSelect={(item) => item.onSelect?.()}
      />
    </header>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/app/components/TopBar.jsx
git commit -m "feat: add TopBar with logo, command palette trigger, user avatar"
```

---

## Task 9: Sidebar Redesign

**Files:**
- Modify: `frontend/src/app/components/Sidebar.jsx`
- Modify: `frontend/src/app/styles/sidebar.css`

- [ ] **Step 1: Rewrite Sidebar.jsx**

Replace the entire Sidebar component with a Linear-style workspace navigator. Key changes:
- Parcels section with collapsible groups (Active, Analyzed, Archived)
- Projects section with status groups
- Views section (Map, Table, 3D)
- Keyboard shortcuts footer
- Status icons (colored dots) next to each parcel
- Remove the old flat nav items (Overview, Finances, Policies, Datasets, Precedents — these become detail panel tabs)
- Keep `useResizable` hook for sidebar drag-resize
- Use Badge component for parcel counts
- Use Kbd component for shortcut hints

The Sidebar receives props: `isCollapsed`, `onToggleCollapse`, `selectedParcels`, `onParcelSelect`, `activeView` (map/table/3d), `onViewChange`, `searchHistory`, `onHistoryClick`.

Parcels are grouped by their `status` field:
- Active = status is 'searching' | 'analyzing' | 'infrastructure'
- Analyzed = status is 'complete'
- Archived = manually archived

Each parcel row shows: status dot (colored per pipeline status) + short address (from `getShortAddress()`).

- [ ] **Step 2: Update sidebar.css**

Update the sidebar CSS to match the new structure:
- Workspace group headers: uppercase, font-xs, text-muted, letter-spacing 0.05em
- Group items: indented 12px, font-sm
- Collapse animation: group content max-height transition
- Active parcel: left border 2px accent, bg accent-bg
- Sidebar footer: shortcuts displayed with Kbd chips
- Hover on parcel rows: bg-tertiary, 80ms transition

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/components/Sidebar.jsx frontend/src/app/styles/sidebar.css
git commit -m "feat: redesign sidebar — workspace groups, parcel status, views, shortcuts"
```

---

## Task 10: DetailPanel (Replaces PolicyPanel + ChatPanel layout)

**Files:**
- Create: `frontend/src/app/components/DetailPanel.jsx`
- Modify: `frontend/src/app/styles/panel.css`

- [ ] **Step 1: Create DetailPanel.jsx**

A container component with tabs at the top (using the Tabs primitive). Renders the appropriate content based on active tab:

```
Tabs: Overview | Policies | Infrastructure | Chat | Documents
```

- Takes `activeTab`, `onTabChange`, and passes through parcel data to content renderers
- Uses `useResizable` hook (axis: 'horizontal', reverse: true) for panel width
- Collapse via button or `⌘]`
- Content for each tab is rendered by the existing PolicyPanel logic (extracted into sections) and ChatPanel

The PolicyPanel's tab rendering (`renderTab()` at line 1971 of PolicyPanel.jsx) becomes the content source. Each "activeNav" case maps to a DetailPanel tab.

ChatPanel renders inside the "Chat" tab, receiving full panel height instead of the constrained 280px bottom bar.

- [ ] **Step 2: Add PipelineStepper to DetailPanel header**

When a parcel is selected, show its current analysis pipeline status above the tabs using the `PipelineStepper` component from `Progress.jsx`.

- [ ] **Step 3: Update panel.css**

- Panel takes full viewport height (below TopBar)
- Tab bar at top with animated underline
- Content area fills remaining height with overflow scroll
- Collapse transition: width 200ms ease-out
- When collapsed, show a thin reopen bar (8px wide, full height, accent hover)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/components/DetailPanel.jsx frontend/src/app/styles/panel.css
git commit -m "feat: add DetailPanel with tabbed content, pipeline stepper, resizable width"
```

---

## Task 11: DashboardView Restructure

**Files:**
- Modify: `frontend/src/app/components/DashboardView.jsx`

- [ ] **Step 1: Restructure DashboardView layout**

Replace the current layout composition (lines 348–512) with:

```
<ToastProvider>
  <div id="dashboard-root" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
    <TopBar ... />
    <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
      <Sidebar ... />
      <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        <MapView ... />  {/* or TableView/3DView based on activeView */}
      </main>
      <DetailPanel ... />
    </div>
    <CommandPalette ... />
  </div>
</ToastProvider>
```

Key changes:
- Add `ToastProvider` wrapper
- Add `TopBar` at top (48px fixed height)
- Remove `SearchBar` from main content (replaced by command palette)
- Remove bottom `ChatPanel` (now inside DetailPanel)
- Add `activeView` state ('map' | 'table' | '3d')
- Add `isCommandPaletteOpen` state
- Add `useKeyboardShortcuts` with all shortcuts
- Add `activeDetailTab` state for DetailPanel tabs
- Keep existing parcel, project, and model state
- Pass `addToast` down via useToast hook for status notifications

- [ ] **Step 2: Wire up command palette actions**

Build the `actions` array for CommandPalette from:
- Search history (recent parcels)
- Navigation actions (switch views, toggle panels)
- Parcel actions (run analysis, generate report, archive)

- [ ] **Step 3: Wire up keyboard shortcuts**

```js
useKeyboardShortcuts([
  { key: 'k', meta: true, action: () => setCommandPaletteOpen(true) },
  { key: '/', meta: true, action: () => setActiveDetailTab('chat') },
  { key: 'b', meta: true, action: () => setIsSidebarCollapsed(c => !c) },
  { key: ']', meta: true, action: () => setIsDetailOpen(d => !d) },
  { key: 'Enter', meta: true, action: () => { /* run analysis */ } },
  { key: '1', meta: true, action: () => setActiveDetailTab('overview') },
  { key: '2', meta: true, action: () => setActiveDetailTab('policies') },
  { key: '3', meta: true, action: () => setActiveDetailTab('infrastructure') },
  { key: '4', meta: true, action: () => setActiveDetailTab('chat') },
  { key: '5', meta: true, action: () => setActiveDetailTab('documents') },
]);
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/components/DashboardView.jsx
git commit -m "feat: restructure dashboard — TopBar, sidebar groups, detail panel, command palette"
```

---

## Task 12: ChatPanel Adaptation

**Files:**
- Modify: `frontend/src/app/components/ChatPanel.jsx`
- Modify: `frontend/src/app/styles/chat.css`

- [ ] **Step 1: Adapt ChatPanel for detail panel rendering**

Key changes:
- Remove `useResizable` for height (no longer a bottom bar)
- Remove the resize handle
- Component now fills its parent container (full height within DetailPanel tab)
- Remove `id="chat-panel"` fixed positioning — now uses `display: flex; flex-direction: column; height: 100%`
- Keep all chat logic (messages, streaming, uploads, plan generation)
- Messages area: `flex: 1; overflow-y: auto`
- Input area: fixed at bottom of container
- Use `EmptyState` component for no-messages state with suggested prompts

- [ ] **Step 2: Update chat.css**

- Remove absolute/fixed positioning
- Chat container: `display: flex; flex-direction: column; height: 100%`
- Messages: `flex: 1; overflow-y: auto; padding: 16px`
- Input: `flex-shrink: 0; padding: 12px 16px; border-top: 1px solid var(--border)`
- Remove `--chat-height` references

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/components/ChatPanel.jsx frontend/src/app/styles/chat.css
git commit -m "feat: adapt ChatPanel for detail panel tab — full height, no resize"
```

---

## Task 13: MapView Full Height + Empty States

**Files:**
- Modify: `frontend/src/app/components/MapView.jsx`
- Modify: `frontend/src/app/styles/map-search.css`

- [ ] **Step 1: Update MapView to take full height**

- Remove bottom padding/margin that accommodated the old chat panel
- Map container fills `100%` of its parent
- Remove any `calc(100vh - var(--chat-height))` height calculations

- [ ] **Step 2: Add empty states to relevant components**

In the Sidebar parcels group, when no parcels exist:
```jsx
<EmptyState
  icon={MapPin}
  title="No parcels yet"
  description="Search for an address or click the map to begin"
  action={<Button variant="solid" size="sm" onClick={onCommandPalette}>Search</Button>}
/>
```

In the DetailPanel when no parcel is selected:
```jsx
<EmptyState
  icon={Building2}
  title="Select a parcel"
  description="Choose a parcel from the sidebar or search to view details"
/>
```

- [ ] **Step 3: Update map-search.css**

Remove chat-height-related calculations. Map fills full remaining height.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/components/MapView.jsx frontend/src/app/styles/map-search.css
git commit -m "feat: full-height map, add empty states for parcels and detail panel"
```

---

## Task 14: Wire ToastProvider + Final Integration

**Files:**
- Modify: `frontend/src/app/layout.tsx` or `frontend/src/app/Providers.jsx`

- [ ] **Step 1: Add ToastProvider to app providers**

If using a Providers wrapper, add `<ToastProvider>` around children. Otherwise, wrap in `DashboardView`.

- [ ] **Step 2: Replace loading states with Skeleton components**

In PolicyPanel/DetailPanel content sections, replace `"Loading..."` text with:
```jsx
<SkeletonGroup lines={4} />
```

- [ ] **Step 3: Add toast notifications for key actions**

In DashboardView, use `useToast()` to show toasts for:
- Parcel added: `addToast({ message: 'Parcel added to workspace', type: 'success' })`
- Analysis started: `addToast({ message: 'Analysis started...', type: 'info' })`
- Analysis complete: `addToast({ message: 'Analysis complete', type: 'success' })`
- Error: `addToast({ message: error.message, type: 'error' })`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/components/DashboardView.jsx frontend/src/app/Providers.jsx frontend/src/app/components/PolicyPanel.jsx
git commit -m "feat: integrate toasts, skeleton loaders, finalize dashboard wiring"
```

---

## Task 15: Update index.md

**Files:**
- Modify: `index.md`

- [ ] **Step 1: Update index.md**

Add entries for all new files created during this implementation:
- `frontend/src/app/components/ui/*` — 17 UI primitives
- `frontend/src/app/components/TopBar.jsx` — Top navigation bar
- `frontend/src/app/components/DetailPanel.jsx` — Tabbed right panel
- `frontend/src/app/hooks/useKeyboardShortcuts.js` — Global keyboard shortcuts
- `frontend/src/app/hooks/useToast.js` — Toast notification hook
- `frontend/src/app/styles/spacing.css` — 4px grid spacing utilities
- Update entries for modified files (DashboardView, Sidebar, ChatPanel, etc.)

- [ ] **Step 2: Commit**

```bash
git add index.md
git commit -m "docs: update index.md with new UI components and modified files"
```
