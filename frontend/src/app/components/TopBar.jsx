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
