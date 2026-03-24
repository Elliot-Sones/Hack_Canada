import { useState, useCallback, useRef, useEffect } from 'react';
import { useSession, signOut } from '../lib/auth-client.js';
import { clearFastApiToken } from '../api.js';
import useResizable from '../hooks/useResizable.js';
import { getShortAddress } from '../lib/parcelState.js';
import Badge from './ui/Badge.jsx';
import Kbd from './ui/Kbd.jsx';

const COLLAPSED_WIDTH = 52;
const DEFAULT_WIDTH = 220;
const MIN_WIDTH = 180;
const MAX_WIDTH = 320;

const STATUS_COLORS = {
    pending:        'var(--text-muted)',
    searching:      '#60a5fa',
    analyzing:      'var(--warning)',
    infrastructure: '#a78bfa',
    complete:       'var(--success)',
    blocked:        'var(--error)',
};

const VIEW_ITEMS = [
    {
        id: 'map', label: 'Map',
        icon: <><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" /><circle cx="12" cy="10" r="3" /></>,
    },
    {
        id: 'table', label: 'Table',
        icon: <><rect x="3" y="3" width="18" height="18" rx="2" ry="2" /><line x1="3" y1="9" x2="21" y2="9" /><line x1="3" y1="15" x2="21" y2="15" /><line x1="9" y1="3" x2="9" y2="21" /></>,
    },
    {
        id: '3d', label: '3D',
        icon: <><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></>,
    },
];

function StatusDot({ status }) {
    const color = STATUS_COLORS[status] || STATUS_COLORS.pending;
    return <span className="parcel-status-dot" style={{ background: color }} />;
}

function SidebarGroup({ label, count, defaultOpen = true, isCollapsed: sidebarCollapsed, children }) {
    const [open, setOpen] = useState(defaultOpen);

    if (sidebarCollapsed) {
        return <div className="sidebar-group collapsed-group">{children}</div>;
    }

    return (
        <div className="sidebar-group">
            <button className="sidebar-group-header" onClick={() => setOpen(!open)}>
                <svg className={`group-chevron${open ? ' open' : ''}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6" />
                </svg>
                <span className="group-label">{label}</span>
                {count > 0 && <Badge color="gray" style={{ marginLeft: 'auto', fontSize: '10px', padding: '0 6px' }}>{count}</Badge>}
            </button>
            {open && <div className="sidebar-group-items">{children}</div>}
        </div>
    );
}

function ParcelRow({ parcel, isActive, onClick, isCollapsed }) {
    const addr = getShortAddress(parcel);
    return (
        <button
            className={`parcel-row${isActive ? ' active' : ''}`}
            onClick={() => onClick(parcel)}
            title={isCollapsed ? addr : undefined}
        >
            <StatusDot status={parcel._pipelineStatus || parcel.status || 'pending'} />
            {!isCollapsed && <span className="parcel-row-label">{addr}</span>}
        </button>
    );
}

function categorizeParcels(parcels) {
    const active = [];
    const analyzed = [];
    for (const p of parcels) {
        const s = p._pipelineStatus || p.status || 'pending';
        if (s === 'complete') analyzed.push(p);
        else active.push(p);
    }
    return { active, analyzed };
}

export default function Sidebar({
    isCollapsed,
    onToggleCollapse,
    selectedParcels = [],
    onParcelSelect,
    activeView = 'map',
    onViewChange,
    searchHistory = [],
    onHistoryClick,
}) {
    const { data: session } = useSession();
    const user = session?.user;

    const { isResizing, handleProps } = useResizable({
        defaultSize: DEFAULT_WIDTH,
        minSize: MIN_WIDTH,
        maxSize: MAX_WIDTH,
        axis: 'horizontal',
        cssVar: isCollapsed ? null : '--sidebar-width',
        disabled: isCollapsed,
    });

    if (isCollapsed) {
        document.documentElement.style.setProperty('--sidebar-width', `${COLLAPSED_WIDTH}px`);
    }

    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const userMenuRef = useRef(null);

    useEffect(() => {
        function handleClickOutside(event) {
            if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
                setIsUserMenuOpen(false);
            }
        }
        if (isUserMenuOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isUserMenuOpen]);

    const logout = useCallback(async () => {
        clearFastApiToken();
        await signOut();
        window.location.href = '/';
    }, []);

    const initials = user
        ? (user.name || user.email || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase()
        : '?';

    const { active: activeParcels, analyzed: analyzedParcels } = categorizeParcels(selectedParcels);
    const activePrimary = selectedParcels[0] || null;

    return (
        <nav id="sidebar" style={{ userSelect: isResizing ? 'none' : undefined }} className="backdrop-blur-xl">
            {/* Logo */}
            <div className="sidebar-top">
                <div className="sidebar-logo">
                    {isCollapsed
                        ? <span className="logo-collapsed"><span className="logo-accent">Co</span></span>
                        : <span className="logo-full"><span className="logo-accent">Co</span>Civil</span>
                    }
                </div>
                <div className="sidebar-divider" />

                {/* PARCELS group */}
                <SidebarGroup label="PARCELS" count={selectedParcels.length} isCollapsed={isCollapsed}>
                    {!isCollapsed && activeParcels.length > 0 && (
                        <div className="sidebar-subgroup">
                            <span className="subgroup-label">Active</span>
                            {activeParcels.map((p, i) => (
                                <ParcelRow key={p.id || i} parcel={p} isActive={activePrimary?.id === p.id} onClick={onParcelSelect} isCollapsed={isCollapsed} />
                            ))}
                        </div>
                    )}
                    {!isCollapsed && analyzedParcels.length > 0 && (
                        <div className="sidebar-subgroup">
                            <span className="subgroup-label">Analyzed</span>
                            {analyzedParcels.map((p, i) => (
                                <ParcelRow key={p.id || i} parcel={p} isActive={activePrimary?.id === p.id} onClick={onParcelSelect} isCollapsed={isCollapsed} />
                            ))}
                        </div>
                    )}
                    {isCollapsed && selectedParcels.map((p, i) => (
                        <ParcelRow key={p.id || i} parcel={p} isActive={activePrimary?.id === p.id} onClick={onParcelSelect} isCollapsed={isCollapsed} />
                    ))}
                    {selectedParcels.length === 0 && !isCollapsed && (
                        <div className="sidebar-empty">No parcels selected</div>
                    )}
                </SidebarGroup>

                {/* PROJECTS group */}
                <SidebarGroup label="PROJECTS" count={0} defaultOpen={false} isCollapsed={isCollapsed}>
                    {!isCollapsed && (
                        <>
                            <div className="sidebar-subgroup">
                                <span className="subgroup-label">In Progress</span>
                                <div className="sidebar-empty">Coming soon</div>
                            </div>
                            <div className="sidebar-subgroup">
                                <span className="subgroup-label">Complete</span>
                                <div className="sidebar-empty">Coming soon</div>
                            </div>
                        </>
                    )}
                </SidebarGroup>

                <div className="sidebar-divider" />

                {/* VIEWS */}
                {!isCollapsed && <span className="sidebar-section-label">VIEWS</span>}
                {VIEW_ITEMS.map(v => (
                    <button
                        key={v.id}
                        className={`nav-item${activeView === v.id ? ' active' : ''}`}
                        onClick={() => onViewChange(v.id)}
                        title={isCollapsed ? v.label : undefined}
                    >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">{v.icon}</svg>
                        <span>{v.label}</span>
                    </button>
                ))}
            </div>

            <div className="sidebar-bottom">
                {/* Shortcuts footer */}
                {!isCollapsed && (
                    <div className="sidebar-shortcuts">
                        <div className="sidebar-divider" />
                        <div className="shortcut-row"><Kbd>&#8984;K</Kbd><span className="shortcut-label">Search</span></div>
                        <div className="shortcut-row"><Kbd>&#8984;/</Kbd><span className="shortcut-label">Chat</span></div>
                        <div className="shortcut-row"><Kbd>&#8984;B</Kbd><span className="shortcut-label">Sidebar</span></div>
                    </div>
                )}

                {/* User section */}
                {user && (
                    <div className="sidebar-user-container" ref={userMenuRef}>
                        <div className="sidebar-divider" />

                        {isUserMenuOpen && (
                            <div className="user-popup backdrop-blur-xl">
                                <div className="user-popup-header">
                                    <div className="user-popup-avatar">
                                        {user.picture
                                            ? <img src={user.picture} alt={user.name || 'User'} />
                                            : <span className="sidebar-user-initials">{initials}</span>
                                        }
                                    </div>
                                    <div className="user-popup-meta">
                                        <span className="user-popup-name">{user.name || 'User'}</span>
                                        <span className="user-popup-email">{user.email}</span>
                                        <span className="user-popup-badge">Pro Plan</span>
                                    </div>
                                </div>
                                <div className="user-popup-divider" />
                                <button className="user-popup-logout" onClick={logout}>
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                                        <polyline points="16 17 21 12 16 7" />
                                        <line x1="21" y1="12" x2="9" y2="12" />
                                    </svg>
                                    Sign Out
                                </button>
                            </div>
                        )}

                        <div
                            className={`sidebar-user interactive ${isUserMenuOpen ? 'active' : ''}`}
                            title={isCollapsed ? (user.name || user.email) : undefined}
                            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                        >
                            <div className="sidebar-user-avatar">
                                {user.picture
                                    ? <img src={user.picture} alt={user.name || 'User'} />
                                    : <span className="sidebar-user-initials">{initials}</span>
                                }
                                <span className="sidebar-user-status" />
                            </div>
                            {!isCollapsed && (
                                <div className="sidebar-user-info">
                                    <span className="sidebar-user-name">{user.name || 'User'}</span>
                                    <span className="sidebar-user-email">{user.email}</span>
                                </div>
                            )}
                            {!isCollapsed && (
                                <svg className="sidebar-user-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ transform: isUserMenuOpen ? 'rotate(180deg)' : 'rotate(0deg)' }}>
                                    <polyline points="18 15 12 9 6 15" />
                                </svg>
                            )}
                        </div>
                        <div className="sidebar-divider" />
                    </div>
                )}

                <button className="nav-item" id="collapse-btn" onClick={onToggleCollapse}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        {isCollapsed ? <polyline points="9 18 15 12 9 6" /> : <polyline points="15 18 9 12 15 6" />}
                    </svg>
                    <span>{isCollapsed ? 'Expand' : 'Collapse'}</span>
                </button>
            </div>

            {!isCollapsed && <div {...handleProps} style={{ ...handleProps.style, right: -2 }} />}
        </nav>
    );
}
