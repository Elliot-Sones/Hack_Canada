const TOOLS = [
  { id: 'select', label: 'S', title: 'Select (V)', enabled: true },
  { id: 'wall', label: 'W', title: 'Draw Wall (W)', enabled: true },
  { id: 'door', label: 'D', title: 'Place Door (D)', enabled: true },
  { id: 'window', label: 'Wi', title: 'Place Window (O)', enabled: true },
  { id: 'room', label: 'R', title: 'Room Type (R)', enabled: true },
  { id: 'measure', label: 'M', title: 'Measure (M)', enabled: true },
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
      {TOOLS.map((tool) => (
        <button
          key={tool.id}
          className={`model-ctrl-btn ${activeTool === tool.id ? 'active' : ''}`}
          onClick={() => tool.enabled && onToolChange(tool.id)}
          title={tool.enabled ? tool.title : tool.tooltip}
          disabled={!tool.enabled}
        >
          {tool.label}
        </button>
      ))}

      <div className="toolbar-divider" />

      <div className="undo-redo-group">
        <button
          className="model-ctrl-btn"
          onClick={onUndo}
          disabled={!canUndo}
          title="Undo (Ctrl+Z)"
        >
          &#x21A9;
        </button>
        <button
          className="model-ctrl-btn"
          onClick={onRedo}
          disabled={!canRedo}
          title="Redo (Ctrl+Shift+Z)"
        >
          &#x21AA;
        </button>
      </div>
    </div>
  );
}
