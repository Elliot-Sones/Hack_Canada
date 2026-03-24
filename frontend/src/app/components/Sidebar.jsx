import { useCallback, useState, useRef, useEffect } from 'react';
import { useSession, signOut } from '../lib/auth-client.js';
import { clearFastApiToken } from '../api.js';
import useResizable from '../hooks/useResizable.js';

const BUILDING_NAV_ITEMS = [
    { id: 'overview', label: 'Overview', icon: (<><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" /><polyline points="9 22 9 12 15 12 15 22" /></>) },
    { id: 'finances', label: 'Finances', icon: (<><line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" /></>) },
    { id: 'policies', label: 'Policies', icon: (<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />) },
    { id: 'datasets', label: 'Datasets', icon: (<><ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" /><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" /></>) },
    { id: 'precedents', label: 'Precedents', icon: (<><circle cx="12" cy="12" r="10" /><polyline points="12 6 12 12 16 14" /></>) },
];

const PROJECTS_ITEM = { id: 'projects', label: 'Projects', icon: (<><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /></>) };

const COLLAPSED_WIDTH = 52;
const DEFAULT_WIDTH = 160;
const MIN_WIDTH = 120;
const MAX_WIDTH = 280;

function shortAddress(item) {
    // Use the short address (e.g. "192 Spadina Avenue") if available,
    // otherwise take just the first segment before the city
    const raw = item.address || item.fullAddress || '';
    const parts = raw.split(',');
    return parts[0].trim();
}

export default function Sidebar({ isCollapsed, onToggleCollapse, activeNav, onNavClick, showHistory, onHistoryClick, onHistoryBack, historyItems, onHistoryItemClick, onDashboardClick, onSettingsClick }) {
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
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isUserMenuOpen]);

    const logout = useCallback(async () => {
        clearFastApiToken();
        await signOut();
        window.location.href = '/';
    }, []);

    const initials = user
        ? (user.name || user.email || '?')
            .split(' ')
            .map((w) => w[0])
            .join('')
            .slice(0, 2)
            .toUpperCase()
        : '?';

    const NAV_ITEMS = BUILDING_NAV_ITEMS;

    return (
        <nav id="sidebar" style={{ userSelect: isResizing ? 'none' : undefined }} className=' backdrop-blur-xl'>
            <div className="sidebar-top">
                <div className="sidebar-logo">
                    {isCollapsed
                        ? <span className="logo-collapsed"><span className="logo-accent">Co</span></span>
                        : <span className="logo-full"><span className="logo-accent">Co</span>Civil</span>
                    }
                </div>
                <div className="sidebar-divider" />

                {showHistory && !isCollapsed ? (
                    <>
                        <button className="history-back-btn" onClick={onHistoryBack}>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" width="16" height="16">
                                <polyline points="15 18 9 12 15 6" />
                            </svg>
                            Back
                        </button>
                        <div className="history-list">
                            {(!historyItems || historyItems.length === 0) ? (
                                <div className="history-empty">No searches yet</div>
                            ) : (
                                historyItems.map((item, idx) => (
                                    <button key={idx} className="history-item" onClick={() => onHistoryItemClick(item)}>
                                        <svg className="history-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                                            <circle cx="12" cy="10" r="3" />
                                        </svg>
                                        <span className="history-item-address">{shortAddress(item)}</span>
                                    </button>
                                ))
                            )}
                        </div>
                    </>
                ) : (
                    <>
                        {NAV_ITEMS.map((item) => (
                            <button
                                key={item.id}
                                className={`nav-item${activeNav === item.id ? ' active' : ''}`}
                                onClick={() => onNavClick(item.id)}
                                title={isCollapsed ? item.label : undefined}
                            >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">{item.icon}</svg>
                                <span>{item.label}</span>
                            </button>
                        ))}
                        {!isCollapsed && (
                            <>
                                <div className="sidebar-divider" />
                                <button
                                    className={`nav-item${activeNav === PROJECTS_ITEM.id ? ' active' : ''}`}
                                    onClick={() => onNavClick(PROJECTS_ITEM.id)}
                                >
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">{PROJECTS_ITEM.icon}</svg>
                                    <span>{PROJECTS_ITEM.label}</span>
                                </button>
                                <button className="nav-item" onClick={onHistoryClick}>
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <circle cx="12" cy="12" r="10" />
                                        <polyline points="12 6 12 12 16 14" />
                                    </svg>
                                    <span>History</span>
                                </button>
                            </>
                        )}
                    </>
                )}
            </div>

            <div className="sidebar-bottom">
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

                                <div className="user-popup-stats">
                                    <div className="user-stat">
                                        <span className="user-stat-val">12</span>
                                        <span className="user-stat-label">Projects</span>
                                    </div>
                                    <div className="user-stat">
                                        <span className="user-stat-val">2.4k</span>
                                        <span className="user-stat-label">Credits</span>
                                    </div>
                                    <div className="user-stat">
                                        <span className="user-stat-val">3</span>
                                        <span className="user-stat-label">Teams</span>
                                    </div>
                                </div>

                                <div className="user-popup-links">
                                    <button className="user-popup-link" onClick={() => { setIsUserMenuOpen(false); onDashboardClick && onDashboardClick(); }}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
                                        </svg>
                                        Dashboard
                                    </button>
                                    <button className="user-popup-link" onClick={() => { setIsUserMenuOpen(false); onSettingsClick && onSettingsClick(); }}>
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                            <circle cx="12" cy="12" r="3" />
                                            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                                        </svg>
                                        Settings
                                    </button>
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
