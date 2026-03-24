"use client";

import { useState, useRef, useCallback, useEffect, useMemo, lazy, Suspense } from 'react';
import { useSession, signOut } from '../lib/auth-client.js';
import { MessageSquare } from 'lucide-react';
import MapView from './MapView.jsx';
import Sidebar from './Sidebar.jsx';
import TopBar from './TopBar.jsx';
import DetailPanel from './DetailPanel.jsx';
import PolicyPanel from './PolicyPanel.jsx';
import ChatPanel from './ChatPanel.jsx';
import CommandPalette from './ui/CommandPalette.jsx';
import ToastProvider from './ui/ToastProvider.jsx';
import InfrastructureLayerControl from './InfrastructureLayerControl.jsx';
import SettingsModal from './SettingsModal.jsx';
import DashboardModal from './DashboardModal.jsx';
import SelectionChips from './SelectionChips.jsx';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts.js';
import { searchParcels, getWatermainsBbox, getSewersBbox, getElectricalBbox, sessionExchange, hasFastApiToken, clearFastApiToken } from '../api.js';
import { buildParcelState, createResolvedParcel, isResolvedParcel, addParcelToSelection, removeParcelFromSelection, toggleParcelInSelection } from '../lib/parcelState.js';
import '../styles/landing.css';

const ModelViewer = lazy(() => import('./ModelViewer.jsx'));
const InfrastructureViewer = lazy(() => import('./InfrastructureViewer.jsx').catch(() => ({ default: () => null })));

export default function DashboardView({ initialAddress, parcelId }) {
  const { data: session, isPending: isLoading } = useSession();
  const user = session?.user;
  const isAuthenticated = !!user;

  // Auto-exchange Better Auth session for FastAPI JWT
  useEffect(() => {
    if (isAuthenticated && !hasFastApiToken()) {
      sessionExchange().catch(() => {});
    }
    if (!isAuthenticated && !isLoading) {
      clearFastApiToken();
    }
  }, [isAuthenticated, isLoading]);

  // --- Parcel selection state ---
  const [selectedParcels, setSelectedParcels] = useState([]);
  const primaryParcel = useMemo(() => selectedParcels.length > 0 ? selectedParcels[selectedParcels.length - 1] : null, [selectedParcels]);
  const isComparisonMode = selectedParcels.length >= 2;

  // --- Layout state ---
  const [isPanelOpen, setIsPanelOpen] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [activeNav, setActiveNav] = useState('overview');
  const [showHistory, setShowHistory] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const [isCommandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [activeDetailTab, setActiveDetailTab] = useState('overview');
  const [isDetailOpen, setIsDetailOpen] = useState(true);

  // --- Data state ---
  const [savedParcels, setSavedParcels] = useState([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDashboardModalOpen, setIsDashboardModalOpen] = useState(false);
  const [modelParams, setModelParams] = useState(null);
  const [isModelOpen, setIsModelOpen] = useState(false);
  const [analyzedUploads, setAnalyzedUploads] = useState([]);
  const [floorPlans, setFloorPlans] = useState(null);
  const [pipelineData, setPipelineData] = useState(null);
  const [projectId, setProjectId] = useState(null);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [activeProjectName, setActiveProjectName] = useState(null);
  const [activePlanId, setActivePlanId] = useState(null);
  const [infraOverlayLayers, setInfraOverlayLayers] = useState(new Set());
  const [infraLayerCounts, setInfraLayerCounts] = useState({});

  // --- Keyboard shortcuts ---
  useKeyboardShortcuts([
    { key: 'k', meta: true, action: () => setCommandPaletteOpen(true) },
    { key: '/', meta: true, action: () => setIsChatExpanded(c => !c) },
    { key: 'b', meta: true, action: () => setIsSidebarCollapsed(c => !c) },
    { key: ']', meta: true, action: () => setIsDetailOpen(d => !d) },
    { key: '1', meta: true, action: () => { setActiveDetailTab('overview'); setActiveNav('overview'); } },
    { key: '2', meta: true, action: () => { setActiveDetailTab('policies'); setActiveNav('policies'); } },
    { key: '3', meta: true, action: () => { setActiveDetailTab('infrastructure'); setActiveNav('datasets'); } },
    { key: '4', meta: true, action: () => { setActiveDetailTab('documents'); setActiveNav('precedents'); } },
  ]);

  const handleUploadAnalyzed = useCallback((upload) => {
    setAnalyzedUploads((prev) => {
      if (prev.some((u) => u.id === upload.id)) return prev;
      return [...prev, upload];
    });
    if (upload.extractedData?.pipeline_network) {
      setPipelineData(upload.extractedData.pipeline_network);
      setProjectId(upload.id);
      setIsModelOpen(true);
      return;
    }
    if (upload.extractedData?.floor_plans) {
      setFloorPlans(upload.extractedData.floor_plans);
      setProjectId(upload.id);
      setIsModelOpen(true);
    }
  }, []);

  // --- Search history ---
  const historyKey = useMemo(
    () => (user?.sub ? `cocivil_history_${user.sub}` : null),
    [user?.sub]
  );

  const [searchHistory, setSearchHistory] = useState(() => []);

  useEffect(() => {
    if (!historyKey) return;
    try {
      const stored = localStorage.getItem(historyKey);
      if (stored) setSearchHistory(JSON.parse(stored));
    } catch {
      // ignore corrupt data
    }
  }, [historyKey]);

  const mapRef = useRef(null);

  const handleLocationSelected = useCallback(async (location) => {
    if (mapRef.current) {
      mapRef.current.flyTo(location.lng, location.lat, 18);
      mapRef.current.setMarker(location.lng, location.lat);
      mapRef.current.setProposedMassing(null, null);
    }

    const parcels = await searchParcels(location.shortAddress || location.address, { lat: location.lat, lng: location.lng });
    const selected = buildParcelState(location, parcels);
    setSelectedParcels(selected ? [selected] : []);
    setIsDetailOpen(true);

    if (historyKey) {
      const entry = {
        address: location.shortAddress || location.address,
        fullAddress: location.address,
        lng: location.lng,
        lat: location.lat,
        timestamp: Date.now(),
      };
      setSearchHistory((prev) => {
        const filtered = prev.filter((h) => h.address !== entry.address);
        const updated = [entry, ...filtered].slice(0, 50);
        localStorage.setItem(historyKey, JSON.stringify(updated));
        return updated;
      });
    }

    if (mapRef.current && isResolvedParcel(selected) && selected.geom) {
      mapRef.current.setParcel(selected.geom);
    } else if (mapRef.current) {
      mapRef.current.setParcel(null);
    }
    if (mapRef.current?.setSelectedParcelIds) {
      mapRef.current.setSelectedParcelIds(selected?.id ? [selected.id] : []);
    }
  }, [historyKey]);

  // Map click handler for parcel bbox layer
  const handleMapParcelClick = useCallback((parcelData, isMultiSelect) => {
    const resolved = createResolvedParcel(
      { shortAddress: parcelData.address, address: parcelData.address },
      { id: parcelData.id, zone_code: parcelData.zone_code, lot_area_m2: parcelData.lot_area_m2, geom: parcelData.geom }
    );
    if (isMultiSelect) {
      setSelectedParcels(prev => toggleParcelInSelection(prev, resolved));
    } else {
      setSelectedParcels([resolved]);
    }
    setIsDetailOpen(true);
  }, []);

  const handleParcelDeselect = useCallback((id) => {
    setSelectedParcels(prev => removeParcelFromSelection(prev, id));
  }, []);

  const handleClearSelection = useCallback(() => {
    setSelectedParcels([]);
    if (mapRef.current?.setSelectedParcelIds) mapRef.current.setSelectedParcelIds([]);
    if (mapRef.current) mapRef.current.setParcel(null);
  }, []);

  const handleSetPrimary = useCallback((id) => {
    setSelectedParcels(prev => {
      const idx = prev.findIndex(p => p.id === id);
      if (idx < 0 || idx === prev.length - 1) return prev;
      const next = [...prev];
      const [item] = next.splice(idx, 1);
      next.push(item);
      return next;
    });
  }, []);

  // Sync map feature-state and primary parcel geometry when selection changes
  useEffect(() => {
    if (!mapRef.current) return;
    const ids = selectedParcels.filter(p => p.id).map(p => p.id);
    if (mapRef.current.setSelectedParcelIds) mapRef.current.setSelectedParcelIds(ids);
    if (primaryParcel && isResolvedParcel(primaryParcel) && primaryParcel.geom) {
      mapRef.current.setParcel(primaryParcel.geom);
    } else {
      mapRef.current.setParcel(null);
    }
  }, [selectedParcels, primaryParcel]);

  // Geocode initial address on mount
  useEffect(() => {
    if (!initialAddress) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(
            initialAddress + ' Toronto Canada'
          )}&format=json&addressdetails=1&limit=1&countrycodes=ca`,
          { headers: { 'Accept-Language': 'en' } }
        );
        const results = await res.json();
        if (cancelled || results.length === 0) return;
        const result = results[0];
        const addr = result.address || {};
        const parts = [];
        if (addr.house_number) parts.push(addr.house_number);
        if (addr.road) parts.push(addr.road);
        let shortAddress = parts.join(' ') || result.display_name.split(',')[0];
        if (addr.city || addr.town) shortAddress += `, ${addr.city || addr.town}`;

        setTimeout(() => {
          if (!cancelled) {
            handleLocationSelected({
              lng: parseFloat(result.lon),
              lat: parseFloat(result.lat),
              address: result.display_name,
              shortAddress,
            });
          }
        }, 500);
      } catch (err) {
        console.error('Geocoding error:', err);
      }
    })();
    return () => { cancelled = true; };
  }, [initialAddress, handleLocationSelected]);

  const handleHistoryClick = useCallback(
    (item) => {
      handleLocationSelected({
        lng: item.lng,
        lat: item.lat,
        address: item.fullAddress,
        shortAddress: item.address,
      });
    },
    [handleLocationSelected]
  );

  const handleSaveParcel = useCallback((parcel) => {
    setSavedParcels((prev) => {
      if (!isResolvedParcel(parcel)) return prev;
      if (prev.some((p) => p.address === parcel.address)) return prev;
      return [...prev, parcel];
    });
  }, []);

  const handleSignOut = useCallback(async () => {
    clearFastApiToken();
    await signOut();
  }, []);

  // Load infrastructure overlay data when layers are toggled or map moves
  useEffect(() => {
    if (infraOverlayLayers.size === 0) return;
    const map = mapRef.current?.getMap();
    if (!map) return;

    let cancelled = false;
    const loadInfraData = async () => {
      try {
        const bounds = map.getBounds();
        const counts = {};
        const promises = [];
        if (infraOverlayLayers.has('watermains')) {
          promises.push(getWatermainsBbox(bounds).then(data => {
            counts.watermains = data?.features?.length || 0;
            if (!cancelled && mapRef.current) mapRef.current.setWatermains(data);
          }));
        }
        if (infraOverlayLayers.has('sewers')) {
          promises.push(getSewersBbox(bounds).then(data => {
            counts.sewers = data?.features?.length || 0;
            if (!cancelled && mapRef.current) mapRef.current.setSewers(data);
          }));
        }
        if (infraOverlayLayers.has('electrical')) {
          promises.push(getElectricalBbox(bounds).then(data => {
            counts.electrical = data?.features?.length || 0;
            if (!cancelled && mapRef.current) mapRef.current.setElectrical(data);
          }));
        }
        await Promise.allSettled(promises);
        if (!cancelled) setInfraLayerCounts(prev => ({ ...prev, ...counts }));
      } catch {
        // Silently fail — infrastructure data is optional context
      }
    };

    loadInfraData();

    const onMoveEnd = () => loadInfraData();
    map.on('moveend', onMoveEnd);
    return () => { cancelled = true; map.off('moveend', onMoveEnd); };
  }, [infraOverlayLayers]);

  // Trigger map resize after layout mounts
  useEffect(() => {
    const timer = setTimeout(() => {
      if (mapRef.current?.getMap()) mapRef.current.getMap().resize();
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  // Sync body classes for CSS
  useEffect(() => {
    if (typeof document === 'undefined') return undefined;

    document.body.classList.toggle('sidebar-collapsed', isSidebarCollapsed);
    document.body.classList.toggle('panel-open', isDetailOpen);

    if (mapRef.current?.getMap()) {
      const styles = getComputedStyle(document.documentElement);
      const left = isSidebarCollapsed ? 52 : (parseInt(styles.getPropertyValue('--sidebar-width')) || 160);
      const right = isDetailOpen ? (parseInt(styles.getPropertyValue('--panel-width')) || 380) : 0;
      const bottom = isChatExpanded ? 280 : 49;
      mapRef.current.getMap().easeTo({
        padding: { left, right, top: 48, bottom },
        duration: 300,
      });
    }

    return () => {
      document.body.classList.remove('sidebar-collapsed');
      document.body.classList.remove('panel-open');
    };
  }, [isSidebarCollapsed, isDetailOpen, isChatExpanded]);

  // --- Command palette actions ---
  const commandActions = useMemo(() => [
    { id: 'chat', label: 'Toggle Chat', kbd: '\u2318/', icon: <MessageSquare size={14} />, group: 'Actions', onSelect: () => setIsChatExpanded(c => !c) },
    { id: 'toggle-sidebar', label: 'Toggle Sidebar', kbd: '\u2318B', group: 'Actions', onSelect: () => setIsSidebarCollapsed(c => !c) },
    { id: 'toggle-panel', label: 'Toggle Detail Panel', kbd: '\u2318]', group: 'Actions', onSelect: () => setIsDetailOpen(d => !d) },
    ...searchHistory.map(h => ({ id: h.address, label: h.address, group: 'Recent', onSelect: () => handleHistoryClick(h) })),
  ], [searchHistory, handleHistoryClick]);

  return (
    <ToastProvider>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        <TopBar
          user={user}
          onCommandPalette={() => setCommandPaletteOpen(true)}
          onSignOut={handleSignOut}
          onSettings={() => setIsSettingsOpen(true)}
        />
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <Sidebar
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(c => !c)}
            activeNav={activeNav}
            onNavClick={(id) => { setActiveNav(id); setActiveDetailTab(id); setIsDetailOpen(true); }}
            showHistory={showHistory}
            onHistoryClick={() => setShowHistory(true)}
            onHistoryBack={() => setShowHistory(false)}
            historyItems={searchHistory}
            onHistoryItemClick={handleHistoryClick}
            onDashboardClick={() => setIsDashboardModalOpen(true)}
            onSettingsClick={() => setIsSettingsOpen(true)}
          />
          <main style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
            <MapView
              ref={mapRef}
              isParcelResolved={primaryParcel !== null}
              onModelOpen={() => setIsModelOpen(true)}
              isPanelOpen={isDetailOpen}
              isSidebarCollapsed={isSidebarCollapsed}
              isChatExpanded={false}
              chatPanelHeight={0}
              isModelOpen={isModelOpen}
              infraOverlayLayers={infraOverlayLayers}
              onParcelClick={handleMapParcelClick}
            />
            {selectedParcels.length > 0 && (
              <SelectionChips
                parcels={selectedParcels}
                primaryId={primaryParcel?.id}
                onSetPrimary={handleSetPrimary}
                onRemove={handleParcelDeselect}
                onClearAll={handleClearSelection}
                isSidebarCollapsed={isSidebarCollapsed}
              />
            )}
            <InfrastructureLayerControl
              mapRef={mapRef}
              infraLayerCounts={infraLayerCounts}
              isChatExpanded={false}
              chatPanelHeight={0}
              isSidebarCollapsed={isSidebarCollapsed}
              onInfraLayerToggle={(layerId, enabled) => {
                setInfraOverlayLayers(prev => {
                  const next = new Set(prev);
                  if (enabled) next.add(layerId);
                  else next.delete(layerId);
                  return next;
                });
              }}
            />
            {activeProjectId && activeProjectName && (
              <div className="project-save-indicator">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="13" height="13">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
                <span className="project-save-name">{activeProjectName}</span>
                <div className="project-save-items">
                  <span className="project-save-item" title="Plans & documents auto-saved">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="11" height="11"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    Plans
                  </span>
                  <span className="project-save-item" title="Chat conversations auto-saved">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="11" height="11"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    Chat
                  </span>
                  <span className="project-save-item" title="File uploads auto-saved">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="11" height="11"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    Files
                  </span>
                </div>
                <button className="project-save-close" onClick={() => { setActiveProjectId(null); setActiveProjectName(null); }} title="Stop saving to project">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="10" height="10">
                    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            )}
          </main>
          <DetailPanel
            activeTab={activeDetailTab}
            onTabChange={(tab) => { setActiveDetailTab(tab); setActiveNav(tab); }}
            isOpen={isDetailOpen}
            onToggle={() => setIsDetailOpen(d => !d)}
            parcel={primaryParcel}
            renderPolicyContent={(navId) => (
              <PolicyPanel
                activeNav={navId}
                parcel={primaryParcel}
                parcels={selectedParcels}
                selectedParcels={selectedParcels}
                isComparisonMode={isComparisonMode}
                savedParcels={savedParcels}
                onSaveParcel={handleSaveParcel}
                onUploadAnalyzed={handleUploadAnalyzed}
                isOpen={true}
                activePlanId={activePlanId}
                activeProjectId={activeProjectId}
                onProjectOpen={(id, name) => { setActiveProjectId(id); setActiveProjectName(name); }}
                onProjectClose={() => { setActiveProjectId(null); setActiveProjectName(null); }}
                embedded={true}
              />
            )}
          />
        </div>
        <ChatPanel
          parcelContext={primaryParcel}
          selectedParcels={selectedParcels}
          isComparisonMode={isComparisonMode}
          modelParams={modelParams}
          onModelUpdate={(params) => { setModelParams(params); setIsModelOpen(true); }}
          onToggleExpand={() => setIsChatExpanded(c => !c)}
          analyzedUploads={analyzedUploads}
          activePlanId={activePlanId}
          activeProjectId={activeProjectId}
          activeProjectName={activeProjectName}
          onPlanComplete={(massing, planId) => {
            if (planId) setActivePlanId(planId);
            if (mapRef.current && primaryParcel?.geom) {
              mapRef.current.setProposedMassing(primaryParcel.geom, massing.height_m || (massing.storeys * 3.5));
            }
            setModelParams({
              storeys: massing.storeys || 0,
              podium_storeys: massing.typology === 'tower_on_podium' ? 4 : 0,
              height_m: massing.height_m || (massing.storeys * 3.5),
              setback_m: massing.assumptions_used?.stepback_m ?? 3.0,
              typology: massing.typology || 'midrise',
              footprint_coverage: massing.lot_coverage_pct ? massing.lot_coverage_pct / 100 : 0.6,
            });
          }}
        />
        <CommandPalette
          open={isCommandPaletteOpen}
          onClose={() => setCommandPaletteOpen(false)}
          actions={commandActions}
          recentItems={searchHistory.slice(0, 5).map(h => ({ id: h.address, label: h.address, onSelect: () => handleHistoryClick(h) }))}
        />
        <Suspense fallback={null}>
          <ModelViewer
            isOpen={isModelOpen && !pipelineData}
            onClose={() => setIsModelOpen(false)}
            parcelGeoJSON={primaryParcel?.geom}
            modelParams={modelParams}
            isPanelOpen={isDetailOpen}
            isSidebarCollapsed={isSidebarCollapsed}
            isChatExpanded={false}
            chatPanelHeight={0}
            floorPlans={floorPlans}
            projectId={projectId}
            parcelId={primaryParcel?.id}
          />
          {pipelineData && (
            <InfrastructureViewer
              isOpen={isModelOpen && !!pipelineData}
              onClose={() => setIsModelOpen(false)}
              modelParams={modelParams}
              isPanelOpen={isDetailOpen}
              isSidebarCollapsed={isSidebarCollapsed}
              isChatExpanded={false}
              pipelineData={pipelineData}
              onPipelineDataChange={setPipelineData}
              assetType="pipeline"
            />
          )}
        </Suspense>
        <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} user={user} />
        <DashboardModal isOpen={isDashboardModalOpen} onClose={() => setIsDashboardModalOpen(false)} />
      </div>
    </ToastProvider>
  );
}
