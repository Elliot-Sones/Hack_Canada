import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import maplibregl from 'maplibre-gl';

function useFadeIn() {
    const ref = useRef(null);
    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    el.classList.add('lp-visible');
                    observer.unobserve(el);
                }
            },
            { threshold: 0.15 }
        );
        observer.observe(el);
        return () => observer.disconnect();
    }, []);
    return ref;
}

const QUERIES = [
    "What's the max building height at 100 Queen St W?",
    "Can I build a 12-storey condo at Yonge and Eglinton?",
    "What are the setback requirements for RM zoning?",
    "Is my property in an inclusionary zoning area?",
    "What's the permitted FSI for this lot?",
    "Do I need a minor variance for a rear addition?",
    "What Official Plan policies apply to this site?",
    "Can I convert this duplex to a fourplex?",
    "What's the angular plane from the north lot line?",
    "Are there heritage overlay restrictions here?",
];

function useTypewriter(strings, typingSpeed = 45, pauseTime = 2200, erasingSpeed = 25) {
    const [displayText, setDisplayText] = useState('');
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isTyping, setIsTyping] = useState(true);

    useEffect(() => {
        const current = strings[currentIndex];
        let timeout;

        if (isTyping) {
            if (displayText.length < current.length) {
                timeout = setTimeout(() => {
                    setDisplayText(current.slice(0, displayText.length + 1));
                }, typingSpeed);
            } else {
                timeout = setTimeout(() => setIsTyping(false), pauseTime);
            }
        } else {
            if (displayText.length > 0) {
                timeout = setTimeout(() => {
                    setDisplayText(displayText.slice(0, -1));
                }, erasingSpeed);
            } else {
                timeout = setTimeout(() => {
                    setCurrentIndex((prev) => (prev + 1) % strings.length);
                    setIsTyping(true);
                }, 0);
            }
        }

        return () => clearTimeout(timeout);
    }, [displayText, currentIndex, isTyping, strings, typingSpeed, pauseTime, erasingSpeed]);

    return displayText;
}

export default function LandingPage({ onNavigate }) {
    const {
        isLoading,
        isAuthenticated,
        error,
        loginWithRedirect: login,
        logout: auth0Logout,
        user,
    } = useAuth0();

    const mapBgRef = useRef(null);
    const mapBgInstanceRef = useRef(null);
    const mapPreviewRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const [address, setAddress] = useState('');
    const typedText = useTypewriter(QUERIES);

    const signup = useCallback(
        () => login({ authorizationParams: { screen_hint: 'signup' } }),
        [login]
    );

    const logout = useCallback(
        () => auth0Logout({ logoutParams: { returnTo: window.location.origin } }),
        [auth0Logout]
    );

    useEffect(() => {
        document.body.classList.add('lp-active');
        return () => document.body.classList.remove('lp-active');
    }, []);

    useEffect(() => {
        if (mapBgInstanceRef.current || !mapBgRef.current) return;
        const bgMap = new maplibregl.Map({
            container: mapBgRef.current,
            style: {
                version: 8,
                sources: {
                    'carto-dark': {
                        type: 'raster',
                        tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
                        tileSize: 256,
                    },
                },
                layers: [{
                    id: 'carto-base',
                    type: 'raster',
                    source: 'carto-dark',
                    paint: {
                        'raster-saturation': -0.1,
                        'raster-brightness-max': 0.7,
                        'raster-contrast': 0.05,
                    },
                }],
            },
            center: [-79.3832, 43.6532],
            zoom: 12,
            interactive: false,
            attributionControl: false,
        });
        mapBgInstanceRef.current = bgMap;
        return () => { bgMap.remove(); mapBgInstanceRef.current = null; };
    }, []);

    useEffect(() => {
        if (mapInstanceRef.current || !mapPreviewRef.current) return;

        const map = new maplibregl.Map({
            container: mapPreviewRef.current,
            style: {
                version: 8,
                sources: {
                    'osm-tiles': {
                        type: 'raster',
                        tiles: [
                            'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
                            'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
                        ],
                        tileSize: 256,
                    },
                },
                layers: [{
                    id: 'osm-base',
                    type: 'raster',
                    source: 'osm-tiles',
                    paint: {
                        'raster-saturation': 0.2,
                        'raster-contrast': 0.05,
                    },
                }],
            },
            center: [-79.3832, 43.6532],
            zoom: 13,
            interactive: true,
            attributionControl: false,
        });

        mapInstanceRef.current = map;
        return () => { map.remove(); mapInstanceRef.current = null; };
    }, []);

    const handleSubmit = useCallback((e) => {
        e.preventDefault();
        if (address.trim()) {
            onNavigate(address.trim());
        }
    }, [address, onNavigate]);

    const demoRef = useFadeIn();
    const howRef = useFadeIn();
    const featRef = useFadeIn();
    const storyRef = useFadeIn();
    const visionRef = useFadeIn();
    const ctaRef = useFadeIn();

    return (
        <div className="lp">
            <div className="lp-bg" ref={mapBgRef} />

            {/* ===== NAVBAR ===== */}
            <nav className="lp-nav">
                <div className="lp-nav-inner">
                    <div className="lp-nav-brand">
                        <div className="lp-nav-icon">
                            <svg viewBox="0 0 20 20" fill="none">
                                <rect x="2" y="2" width="7" height="7" rx="1.5" fill="#c8a55c" />
                                <rect x="11" y="2" width="7" height="7" rx="1.5" fill="#c8a55c" opacity="0.5" />
                                <rect x="2" y="11" width="7" height="7" rx="1.5" fill="#c8a55c" opacity="0.5" />
                                <rect x="11" y="11" width="7" height="7" rx="1.5" fill="#c8a55c" opacity="0.25" />
                            </svg>
                        </div>
                        <div className="lp-nav-logo">CoCivil</div>
                    </div>
                    <div className="lp-nav-center">
                        <a href="#how-it-works" className="lp-nav-item">How It Works</a>
                        <a href="#features" className="lp-nav-item">Features</a>
                        <a href="#about" className="lp-nav-item">About</a>
                    </div>
                    <div className="lp-nav-actions">
                        {isLoading ? (
                            <span className="lp-nav-loading">Loading…</span>
                        ) : isAuthenticated && (
                            <>
                                {user?.picture && (
                                    <img
                                        src={user.picture}
                                        alt={user.name || 'User'}
                                        className="lp-nav-avatar"
                                    />
                                )}
                                <span className="lp-nav-greeting">
                                    {user?.name || user?.email}
                                </span>
                                <div className="lp-nav-divider" />
                                <button className="lp-nav-link" onClick={logout}>
                                    Sign Out
                                </button>
                            </>
                        )}
                        <button className="lp-nav-cta" onClick={() => onNavigate('')}>
                            Get Started
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                <path d="M5 12h14M12 5l7 7-7 7" />
                            </svg>
                        </button>
                    </div>
                </div>
            </nav>

            {/* ===== HERO ===== */}
            <section className="lp-hero">
                <div className="lp-hero-content">
                    <div className="lp-hero-left">
                        <div className="lp-typewriter-wrap">
                            <h1 className="lp-typewriter">
                                {typedText}
                                <span className="lp-cursor" />
                            </h1>
                        </div>
                        <p className="lp-motto">
                            The intelligence layer between policy and design. We read the
                            city's rules so you don't have to.
                        </p>
                    </div>

                    <div className="lp-hero-right">
                        <div className="lp-map-preview">
                            <div className="lp-map-container" ref={mapPreviewRef} />
                            <div className="lp-map-shine" />
                        </div>

                        <form className="lp-address-bar" onSubmit={handleSubmit}>
                            <svg
                                className="lp-address-icon"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                            >
                                <circle cx="11" cy="11" r="8" />
                                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                            </svg>
                            <input
                                type="text"
                                className="lp-address-input"
                                placeholder="Enter an address to get started..."
                                value={address}
                                onChange={(e) => setAddress(e.target.value)}
                            />
                            <kbd className="lp-address-kbd">↵</kbd>
                        </form>
                    </div>
                </div>

                <div className="lp-scroll-hint">
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.5"
                    >
                        <polyline points="6 9 12 15 18 9" />
                    </svg>
                </div>
            </section>

            {/* ===== PRODUCT DEMO ===== */}
            <section className="lp-section lp-demo lp-fade" ref={demoRef}>
                <div className="lp-demo-inner">
                    <div className="lp-section-label" style={{textAlign: 'center'}}>See It In Action</div>
                    <h2 className="lp-section-heading" style={{textAlign: 'center', maxWidth: 600, margin: '0 auto 40px'}}>
                        Your entire due diligence workflow, one screen
                    </h2>
                    <div className="lp-browser">
                        <div className="lp-browser-bar">
                            <div className="lp-browser-dots">
                                <span /><span /><span />
                            </div>
                            <div className="lp-browser-url">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2" /><path d="M7 11V7a5 5 0 0110 0v4" /></svg>
                                cocivils.com/dashboard
                            </div>
                        </div>
                        <div className="lp-browser-content">
                            {/* Sidebar */}
                            <div className="lp-demo-sidebar">
                                <div className="lp-demo-logo">CoCivil</div>
                                <div className="lp-demo-nav-item lp-demo-active">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
                                    Search
                                </div>
                                <div className="lp-demo-nav-item">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" /></svg>
                                    Assistant
                                </div>
                                <div className="lp-demo-nav-item">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                                    Documents
                                </div>
                            </div>

                            {/* Map area */}
                            <div className="lp-demo-map">
                                <div className="lp-demo-map-label">Interactive Zoning Map</div>
                                <div className="lp-demo-parcel">
                                    <div className="lp-demo-parcel-outline" />
                                </div>
                                <div className="lp-demo-pin">
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="#c8a55c" stroke="#c8a55c" strokeWidth="1"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 1118 0z" /><circle cx="12" cy="10" r="3" fill="#0a0a0a" /></svg>
                                </div>
                                <div className="lp-demo-search-bar">
                                    <span className="lp-demo-search-icon">⌕</span>
                                    100 Queen Street West, Toronto
                                </div>
                            </div>

                            {/* Right panel */}
                            <div className="lp-demo-panel">
                                <div className="lp-demo-panel-title">Zoning Analysis</div>
                                <div className="lp-demo-address">100 Queen St W</div>
                                <div className="lp-demo-zone-badge">CR 3.0 (c2.0; r2.5) SS2</div>

                                <div className="lp-demo-row">
                                    <span className="lp-demo-label">Max Height</span>
                                    <span className="lp-demo-value">65.0 m</span>
                                </div>
                                <div className="lp-demo-row">
                                    <span className="lp-demo-label">Max FSI</span>
                                    <span className="lp-demo-value">3.0</span>
                                </div>
                                <div className="lp-demo-row">
                                    <span className="lp-demo-label">Min Setback (Front)</span>
                                    <span className="lp-demo-value">3.0 m</span>
                                </div>
                                <div className="lp-demo-row">
                                    <span className="lp-demo-label">Lot Coverage</span>
                                    <span className="lp-demo-value">80%</span>
                                </div>

                                <div className="lp-demo-divider" />

                                <div className="lp-demo-panel-title" style={{fontSize: '0.7rem'}}>Official Plan</div>
                                <div className="lp-demo-tag">Mixed Use Areas</div>
                                <div className="lp-demo-tag">Downtown &amp; Central Waterfront</div>

                                <div className="lp-demo-divider" />

                                <div className="lp-demo-panel-title" style={{fontSize: '0.7rem'}}>Overlays</div>
                                <div className="lp-demo-tag lp-demo-tag-warn">Heritage Conservation District</div>
                                <div className="lp-demo-tag lp-demo-tag-warn">Site Plan Control Area</div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== HOW IT WORKS ===== */}
            <section id="how-it-works" className="lp-section lp-how lp-fade" ref={howRef}>
                <div className="lp-how-inner">
                    <div className="lp-section-label" style={{textAlign: 'center'}}>How It Works</div>
                    <h2 className="lp-section-heading" style={{textAlign: 'center', maxWidth: 600, margin: '0 auto 48px'}}>
                        From address to analysis in three steps
                    </h2>
                    <div className="lp-steps">
                        <div className="lp-step">
                            <div className="lp-step-num">1</div>
                            <svg className="lp-step-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 1118 0z" />
                                <circle cx="12" cy="10" r="3" />
                            </svg>
                            <h3 className="lp-step-title">Enter an Address</h3>
                            <p className="lp-step-desc">Drop in any Ontario property address</p>
                        </div>
                        <div className="lp-step">
                            <div className="lp-step-num">2</div>
                            <svg className="lp-step-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M12 20V10" />
                                <path d="M18 20V4" />
                                <path d="M6 20v-4" />
                            </svg>
                            <h3 className="lp-step-title">We Analyze the Rules</h3>
                            <p className="lp-step-desc">Zoning, Official Plan, overlays, heritage — parsed instantly</p>
                        </div>
                        <div className="lp-step">
                            <div className="lp-step-num">3</div>
                            <svg className="lp-step-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                                <polyline points="14 2 14 8 20 8" />
                                <line x1="16" y1="13" x2="8" y2="13" />
                                <line x1="16" y1="17" x2="8" y2="17" />
                            </svg>
                            <h3 className="lp-step-title">Get Your Report</h3>
                            <p className="lp-step-desc">Compliance matrix, risk flags, and submission-ready documents</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== WHAT YOU GET ===== */}
            <section id="features" className="lp-section lp-features lp-fade" ref={featRef}>
                <div className="lp-features-inner">
                    <div className="lp-section-label" style={{textAlign: 'center'}}>What You Get</div>
                    <h2 className="lp-section-heading" style={{textAlign: 'center', maxWidth: 600, margin: '0 auto 48px'}}>
                        Everything you need, nothing you don't
                    </h2>
                    <div className="lp-cards">
                        <div className="lp-card">
                            <svg className="lp-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M9 11l3 3L22 4" />
                                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
                            </svg>
                            <h3 className="lp-card-title">Zoning Compliance</h3>
                            <p className="lp-card-desc">Instant dimensional checks against By-law 569-2013</p>
                        </div>
                        <div className="lp-card">
                            <svg className="lp-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="2" y1="12" x2="22" y2="12" />
                                <path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z" />
                            </svg>
                            <h3 className="lp-card-title">Policy Intelligence</h3>
                            <p className="lp-card-desc">Official Plan, PPS, and overlay analysis in seconds</p>
                        </div>
                        <div className="lp-card">
                            <svg className="lp-card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <path d="M4 19.5A2.5 2.5 0 016.5 17H20" />
                                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z" />
                            </svg>
                            <h3 className="lp-card-title">Submission Packages</h3>
                            <p className="lp-card-desc">Planning rationale, compliance matrix, and precedent reports</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* ===== OUR STORY ===== */}
            <section id="about" className="lp-section lp-story lp-fade" ref={storyRef}>
                <div className="lp-section-inner">
                    <div className="lp-section-label">Our Story</div>
                    <h2 className="lp-section-heading">
                        We started where every developer starts — buried in PDFs.
                    </h2>
                    <p className="lp-section-body">
                        Zoning bylaws scattered across hundreds of pages. Official Plan
                        policies in one tab, setback tables in another, heritage overlays
                        in a third. Hours wasted before a single sketch is drawn. We built
                        CoCivil because we lived this problem — and because we knew
                        AI could solve it. Our platform reads the city's rules so you
                        don't have to, turning weeks of due diligence into minutes of
                        conversation.
                    </p>
                </div>
            </section>

            {/* ===== OUR VISION ===== */}
            <section className="lp-section lp-vision lp-fade" ref={visionRef}>
                <div className="lp-section-inner lp-align-right">
                    <div className="lp-section-label">Our Vision</div>
                    <h2 className="lp-section-heading">
                        A world where building the right thing is the easy thing.
                    </h2>
                    <p className="lp-section-body">
                        Every city has rules. Most are written for lawyers, not builders.
                        We envision a future where any developer, architect, or planner
                        can instantly understand what's possible on any parcel — and make
                        smarter decisions from day one. CoCivil is the intelligence
                        layer between policy and design, making cities faster to build and
                        better to live in.
                    </p>
                </div>
            </section>

            {/* ===== FINAL CTA ===== */}
            <section className="lp-section lp-cta-section lp-fade" ref={ctaRef}>
                <div className="lp-cta-inner">
                    <h2 className="lp-cta-heading">Ready to streamline your due diligence?</h2>
                    <p className="lp-cta-sub">Start analyzing any Ontario property in seconds.</p>
                    <button className="lp-cta-btn" onClick={() => onNavigate('')}>
                        Get Started
                    </button>
                </div>
            </section>

            {/* ===== FOOTER ===== */}
            <footer className="lp-footer">
                <div className="lp-footer-inner">
                    <div className="lp-footer-links">
                        <span className="lp-footer-link">About</span>
                        <span className="lp-footer-sep" />
                        <span className="lp-footer-link">Contact</span>
                    </div>
                    <div className="lp-footer-copy">
                        <span>&copy; 2026 CoCivil</span>
                        <span className="lp-footer-sep" />
                        <span>Toronto, Canada</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}