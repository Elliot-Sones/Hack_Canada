// SVG Icons
const SelectIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M6 6l-2-2M6 6h4v4h12v12H6V6z" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="6" cy="6" r="1" fill="currentColor" />
  </svg>
);

const WallIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor">
    <rect x="4" y="8" width="16" height="8" fill="currentColor" />
  </svg>
);

const DoorIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="4" y="3" width="14" height="18" />
    <circle cx="16" cy="12" r="1.5" fill="currentColor" />
    <path d="M4 12h12" />
  </svg>
);

const WindowIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="3" y="3" width="18" height="18" />
    <line x1="12" y1="3" x2="12" y2="21" />
    <line x1="3" y1="12" x2="21" y2="12" />
  </svg>
);

const RoomIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <rect x="4" y="4" width="16" height="16" />
    <line x1="4" y1="12" x2="20" y2="12" />
    <line x1="12" y1="4" x2="12" y2="20" />
  </svg>
);

const DeleteIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <polyline points="3 6 5 6 21 6" />
    <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6m3 0V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
    <line x1="10" y1="11" x2="10" y2="17" />
    <line x1="14" y1="11" x2="14" y2="17" />
  </svg>
);

const MeasureIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <line x1="3" y1="12" x2="21" y2="12" />
    <line x1="3" y1="9" x2="3" y2="15" />
    <line x1="21" y1="9" x2="21" y2="15" />
    <path d="M12 12l-3 3m0-6l3 3" strokeLinecap="round" />
  </svg>
);

const TOOLS = [
  { id: 'select', title: 'Select (V)', icon: SelectIcon, enabled: true },
  { id: 'wall', title: 'Wall (W)', icon: WallIcon, enabled: true },
  { id: 'door', title: 'Door (D)', icon: DoorIcon, enabled: true },
  { id: 'window', title: 'Window (O)', icon: WindowIcon, enabled: true },
  { id: 'delete', title: 'Delete (X)', icon: DeleteIcon, enabled: true },
];

export default function EditorToolbar({
  activeTool,
  onToolChange,
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  showDimensions,
  onToggleDimensions,
}) {
  return (
    <div className="floorplan-toolbar">
      {TOOLS.map((tool) => {
        const IconComponent = tool.icon;
        return (
          <button
            key={tool.id}
            className={`toolbar-icon-btn ${activeTool === tool.id ? 'active' : ''}`}
            onClick={() => tool.enabled && onToolChange(tool.id)}
            title={tool.enabled ? tool.title : tool.title}
            disabled={!tool.enabled}
          >
            <IconComponent />
          </button>
        );
      })}

      <div className="toolbar-divider" />

      <div className="undo-redo-group">
        <button
          className="toolbar-icon-btn"
          onClick={onUndo}
          disabled={!canUndo}
          title="Undo (Ctrl+Z)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 7v6h6M21 17a9 9 0 00-9-9 9 9 0 00-6 2.3L3 13" />
          </svg>
        </button>
        <button
          className="toolbar-icon-btn"
          onClick={onRedo}
          disabled={!canRedo}
          title="Redo (Ctrl+Y)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 7v6h-6M3 17a9 9 0 019-9 9 9 0 016 2.3l3 2.7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
