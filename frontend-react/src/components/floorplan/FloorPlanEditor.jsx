import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Stage, Layer, Line, Circle } from 'react-konva';
import { ensureIds, generateId } from '../../lib/floorPlanHelpers.js';
import { snapToGrid, snapToEndpoint, updateRoomsAfterWallEdit, distanceBetweenPoints } from '../../lib/wallGeometry.js';
import WallLayer from './layers/WallLayer.jsx';
import RoomLayer from './layers/RoomLayer.jsx';
import OpeningLayer from './layers/OpeningLayer.jsx';
import DimensionLayer from './layers/DimensionLayer.jsx';
import ComplianceBadgeLayer from './layers/ComplianceBadgeLayer.jsx';
import CompliancePanel from './panels/CompliancePanel.jsx';
import EditorToolbar from './panels/EditorToolbar.jsx';
import ScaleCalibration from './panels/ScaleCalibration.jsx';
import RoomTypeSelector from './panels/RoomTypeSelector.jsx';
import WallProperties from './panels/WallProperties.jsx';
import './FloorPlanEditor.css';

const MAX_HISTORY = 50;

export default function FloorPlanEditor({
  floorPlans,
  activeFloor,
  onFloorPlansChange,
  parcelId,
}) {
  const stageRef = useRef(null);
  const containerRef = useRef(null);

  // Stage viewport
  const [stageSize, setStageSize] = useState({ width: 800, height: 600 });
  const [stageScale, setStageScale] = useState(1);
  const [stagePosition, setStagePosition] = useState({ x: 0, y: 0 });

  // Editor state
  const [selectedElementId, setSelectedElementId] = useState(null);
  const [selectedElementType, setSelectedElementType] = useState(null); // 'room' | 'wall' | 'opening' | null
  const [activeTool, setActiveTool] = useState('select');
  const [scaleCalibrated, setScaleCalibrated] = useState(true);
  const [showDimensions, setShowDimensions] = useState(true);

  // Room type popover
  const [roomTypePopover, setRoomTypePopover] = useState(null);

  // Wall drawing state
  const [wallDrawStart, setWallDrawStart] = useState(null);
  const [wallDrawPreview, setWallDrawPreview] = useState(null);

  // Compliance
  const [complianceResult, setComplianceResult] = useState(null);
  const [complianceLoading, setComplianceLoading] = useState(false);
  const complianceTimerRef = useRef(null);

  // Undo/redo
  const [editHistory, setEditHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  // Ensure IDs on mount / when floorPlans change
  const normalizedPlans = useMemo(() => ensureIds(floorPlans), [floorPlans]);

  const currentFloor = useMemo(() => {
    if (!normalizedPlans?.floor_plans) return null;
    if (activeFloor != null) {
      return normalizedPlans.floor_plans.find((f) => f.floor_number === activeFloor) || null;
    }
    return normalizedPlans.floor_plans[0] || null;
  }, [normalizedPlans, activeFloor]);

  const currentFloorIndex = useMemo(() => {
    if (!normalizedPlans?.floor_plans || !currentFloor) return 0;
    const idx = normalizedPlans.floor_plans.findIndex(
      (f) => f.floor_number === currentFloor.floor_number
    );
    return idx >= 0 ? idx : 0;
  }, [normalizedPlans, currentFloor]);

  // Derive selected wall object for WallProperties panel
  const selectedWall = useMemo(() => {
    if (selectedElementType !== 'wall' || !selectedElementId || !currentFloor?.walls) return null;
    return currentFloor.walls.find((w) => w.id === selectedElementId) || null;
  }, [selectedElementId, selectedElementType, currentFloor]);

  // Resize observer for container
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        setStageSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });

    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Fit-to-view on mount
  useEffect(() => {
    if (!currentFloor) return;

    const points = [];
    currentFloor.walls?.forEach((w) => {
      points.push(w.start, w.end);
    });
    currentFloor.rooms?.forEach((r) => {
      r.polygon?.forEach((p) => points.push(p));
    });

    if (points.length === 0) return;

    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    for (const [x, y] of points) {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    }

    const dataW = maxX - minX || 1;
    const dataH = maxY - minY || 1;
    const padding = 60;
    const scaleX = (stageSize.width - padding * 2) / dataW;
    const scaleY = (stageSize.height - padding * 2) / dataH;
    const fitScale = Math.min(scaleX, scaleY, 100);

    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;

    setStageScale(fitScale);
    setStagePosition({
      x: stageSize.width / 2 - centerX * fitScale,
      y: stageSize.height / 2 - centerY * fitScale,
    });
  }, [currentFloor, stageSize]);

  // Initialize undo history
  useEffect(() => {
    if (normalizedPlans && editHistory.length === 0) {
      setEditHistory([JSON.parse(JSON.stringify(normalizedPlans))]);
      setHistoryIndex(0);
    }
  }, [normalizedPlans]);

  // Debounced compliance check
  const runComplianceCheck = useCallback(
    (plans) => {
      if (complianceTimerRef.current) clearTimeout(complianceTimerRef.current);

      complianceTimerRef.current = setTimeout(async () => {
        setComplianceLoading(true);
        try {
          const floorPlanData = plans?.floor_plans?.[0] || currentFloor;
          if (!floorPlanData) return;
          const res = await fetch('/api/v1/compliance/interior', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ floor_plan: floorPlanData, ceiling_height_m: 2.7 }),
          });
          if (res.ok) {
            setComplianceResult(await res.json());
          }
        } catch {
          // silent fail for compliance
        } finally {
          setComplianceLoading(false);
        }
      }, 300);
    },
    [parcelId, currentFloor]
  );

  // Deep-clone helper
  const clonePlans = useCallback(() => {
    return JSON.parse(JSON.stringify(normalizedPlans));
  }, [normalizedPlans]);

  // Push change: update parent, record undo snapshot, trigger compliance
  const pushChange = useCallback(
    (newPlans) => {
      onFloorPlansChange?.(newPlans);

      setEditHistory((prev) => {
        const trimmed = prev.slice(0, historyIndex + 1);
        const next = [...trimmed, JSON.parse(JSON.stringify(newPlans))];
        if (next.length > MAX_HISTORY) {
          return next.slice(next.length - MAX_HISTORY);
        }
        return next;
      });
      setHistoryIndex((prev) => Math.min(prev + 1, MAX_HISTORY - 1));

      runComplianceCheck(newPlans);
    },
    [onFloorPlansChange, historyIndex, runComplianceCheck]
  );

  // Undo / Redo
  const undo = useCallback(() => {
    if (historyIndex <= 0) return;
    const newIdx = historyIndex - 1;
    setHistoryIndex(newIdx);
    const snapshot = editHistory[newIdx];
    onFloorPlansChange?.(JSON.parse(JSON.stringify(snapshot)));
    runComplianceCheck(snapshot);
  }, [historyIndex, editHistory, onFloorPlansChange, runComplianceCheck]);

  const redo = useCallback(() => {
    if (historyIndex >= editHistory.length - 1) return;
    const newIdx = historyIndex + 1;
    setHistoryIndex(newIdx);
    const snapshot = editHistory[newIdx];
    onFloorPlansChange?.(JSON.parse(JSON.stringify(snapshot)));
    runComplianceCheck(snapshot);
  }, [historyIndex, editHistory, onFloorPlansChange, runComplianceCheck]);

  // ---------- Selection handlers ----------
  const handleDeselect = useCallback(() => {
    setSelectedElementId(null);
    setSelectedElementType(null);
    setRoomTypePopover(null);
  }, []);

  const handleSelectRoom = useCallback((roomId, evt) => {
    setSelectedElementId(roomId);
    setSelectedElementType('room');
    setRoomTypePopover(null);

    // If room type tool is active, show the popover
    if (activeTool === 'room') {
      const room = currentFloor?.rooms?.find((r) => r.id === roomId);
      if (room) {
        const stage = stageRef.current;
        const pointerPos = stage?.getPointerPosition();
        setRoomTypePopover({
          roomId,
          currentType: room.room_type || 'other',
          position: {
            x: pointerPos?.x ?? 200,
            y: pointerPos?.y ?? 200,
          },
        });
      }
    }
  }, [activeTool, currentFloor]);

  const handleSelectOpening = useCallback((openingId) => {
    setSelectedElementId(openingId);
    setSelectedElementType('opening');
    setRoomTypePopover(null);
  }, []);

  // ---------- Room type editing ----------
  const handleRoomTypeChange = useCallback((newType) => {
    if (!roomTypePopover) return;
    const plans = clonePlans();
    const floor = plans.floor_plans[currentFloorIndex];
    const room = floor.rooms?.find((r) => r.id === roomTypePopover.roomId);
    if (room) {
      room.room_type = newType;
      pushChange(plans);
    }
    setRoomTypePopover(null);
  }, [roomTypePopover, clonePlans, currentFloorIndex, pushChange]);

  // ---------- Wall property editing ----------
  const handleWallUpdate = useCallback((updatedWall) => {
    const plans = clonePlans();
    const floor = plans.floor_plans[currentFloorIndex];
    const idx = floor.walls?.findIndex((w) => w.id === updatedWall.id);
    if (idx >= 0) {
      floor.walls[idx] = { ...floor.walls[idx], ...updatedWall };
      pushChange(plans);
    }
  }, [clonePlans, currentFloorIndex, pushChange]);

  // ---------- Wall deletion ----------
  const handleWallDelete = useCallback((wallId) => {
    const plans = clonePlans();
    const floor = plans.floor_plans[currentFloorIndex];
    floor.walls = floor.walls?.filter((w) => w.id !== wallId) || [];
    floor.openings = floor.openings?.filter((o) => o.wall_id !== wallId) || [];
    pushChange(plans);
    handleDeselect();
  }, [clonePlans, currentFloorIndex, pushChange, handleDeselect]);

  // ---------- Wall endpoint dragging ----------
  const handleWallEndpointDrag = useCallback((wallId, endpoint, newPos) => {
    const plans = clonePlans();
    const floor = plans.floor_plans[currentFloorIndex];
    const wall = floor.walls?.find((w) => w.id === wallId);
    if (!wall) return;

    const snapped = snapToEndpoint(newPos, floor.walls || []);
    const oldPoint = endpoint === 'start' ? [...wall.start] : [...wall.end];

    if (endpoint === 'start') {
      wall.start = snapped;
    } else {
      wall.end = snapped;
    }

    floor.rooms = updateRoomsAfterWallEdit(floor.rooms, oldPoint, snapped);
    pushChange(plans);
  }, [clonePlans, currentFloorIndex, pushChange]);

  // ---------- Door/Window placement on wall click ----------
  const handleWallClickForOpening = useCallback((wallId) => {
    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    const worldX = (pointer.x - stagePosition.x) / stageScale;
    const worldY = (pointer.y - stagePosition.y) / stageScale;

    const plans = clonePlans();
    const floor = plans.floor_plans[currentFloorIndex];
    const wall = floor.walls?.find((w) => w.id === wallId);
    if (!wall) return;

    const dx = wall.end[0] - wall.start[0];
    const dy = wall.end[1] - wall.start[1];
    const len = Math.sqrt(dx * dx + dy * dy);
    if (len === 0) return;

    const t = ((worldX - wall.start[0]) * dx + (worldY - wall.start[1]) * dy) / (len * len);
    const clampedT = Math.max(0.05, Math.min(0.95, t));
    const offset = clampedT * len;

    const openingType = activeTool === 'door' ? 'door' : 'window';
    const defaultWidth = openingType === 'door' ? 0.9 : 1.0;

    if (!floor.openings) floor.openings = [];
    const newOpening = {
      id: generateId('o'),
      type: openingType,
      wall_id: wallId,
      offset_along_wall: offset,
      width_m: defaultWidth,
    };
    if (openingType === 'door') {
      newOpening.swing_direction = 'inward';
    }
    floor.openings.push(newOpening);
    pushChange(plans);
    setSelectedElementId(newOpening.id);
    setSelectedElementType('opening');
  }, [activeTool, stagePosition, stageScale, clonePlans, currentFloorIndex, pushChange]);

  // ---------- Wall select (must be after handleWallClickForOpening) ----------
  const handleSelectWall = useCallback((wallId) => {
    if (activeTool === 'door' || activeTool === 'window') {
      handleWallClickForOpening(wallId);
      return;
    }
    setSelectedElementId(wallId);
    setSelectedElementType('wall');
    setRoomTypePopover(null);
  }, [activeTool, handleWallClickForOpening]);

  // ---------- Opening dragging ----------
  const handleOpeningDrag = useCallback((openingId, newOffset) => {
    const plans = clonePlans();
    const floor = plans.floor_plans[currentFloorIndex];
    const opening = floor.openings?.find((o) => o.id === openingId);
    if (opening) {
      opening.offset_along_wall = newOffset;
      pushChange(plans);
    }
  }, [clonePlans, currentFloorIndex, pushChange]);

  // ---------- Stage click for wall drawing / deselect ----------
  const handleStageClick = useCallback((e) => {
    if (e.target !== e.target.getStage()) return;

    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    const worldX = (pointer.x - stagePosition.x) / stageScale;
    const worldY = (pointer.y - stagePosition.y) / stageScale;
    const worldPoint = [worldX, worldY];

    if (activeTool === 'wall') {
      const snapped = currentFloor?.walls?.length
        ? snapToEndpoint(worldPoint, currentFloor.walls)
        : snapToGrid(worldPoint);

      if (!wallDrawStart) {
        setWallDrawStart(snapped);
        setWallDrawPreview(snapped);
      } else {
        if (distanceBetweenPoints(wallDrawStart, snapped) > 0.1) {
          const plans = clonePlans();
          const floor = plans.floor_plans[currentFloorIndex];
          if (!floor.walls) floor.walls = [];
          floor.walls.push({
            id: generateId('w'),
            start: wallDrawStart,
            end: snapped,
            type: 'interior',
            load_bearing: 'unknown',
            thickness_m: 0.15,
          });
          pushChange(plans);
        }
        setWallDrawStart(null);
        setWallDrawPreview(null);
      }
    } else if (activeTool === 'select') {
      handleDeselect();
    }
  }, [activeTool, wallDrawStart, stagePosition, stageScale, currentFloor, clonePlans, currentFloorIndex, pushChange, handleDeselect]);

  const handleStageMouseMove = useCallback((e) => {
    if (activeTool !== 'wall' || !wallDrawStart) return;
    const stage = stageRef.current;
    if (!stage) return;
    const pointer = stage.getPointerPosition();
    const worldX = (pointer.x - stagePosition.x) / stageScale;
    const worldY = (pointer.y - stagePosition.y) / stageScale;
    const snapped = currentFloor?.walls?.length
      ? snapToEndpoint([worldX, worldY], currentFloor.walls)
      : snapToGrid([worldX, worldY]);
    setWallDrawPreview(snapped);
  }, [activeTool, wallDrawStart, stagePosition, stageScale, currentFloor]);

  // ---------- Delete selected element ----------
  const deleteSelected = useCallback(() => {
    if (!selectedElementId || !selectedElementType) return;

    if (selectedElementType === 'wall') {
      const wall = currentFloor?.walls?.find((w) => w.id === selectedElementId);
      if (!wall || wall.load_bearing === 'yes') return;
      handleWallDelete(selectedElementId);
    } else if (selectedElementType === 'opening') {
      const plans = clonePlans();
      const floor = plans.floor_plans[currentFloorIndex];
      floor.openings = floor.openings?.filter((o) => o.id !== selectedElementId) || [];
      pushChange(plans);
      handleDeselect();
    }
  }, [selectedElementId, selectedElementType, currentFloor, handleWallDelete, clonePlans, currentFloorIndex, pushChange, handleDeselect]);

  // ---------- Keyboard shortcuts ----------
  useEffect(() => {
    const handler = (e) => {
      // Tool shortcuts (no modifier keys)
      if (!e.ctrlKey && !e.metaKey && !e.altKey) {
        switch (e.key) {
          case 'v': case 'V': setActiveTool('select'); return;
          case 'w': setActiveTool('wall'); return;
          case 'r': setActiveTool('room'); return;
          case 'd': setActiveTool('door'); return;
          case 'o': setActiveTool('window'); return;
          case 'm': setActiveTool('measure'); return;
          case 'Escape':
            if (wallDrawStart) {
              setWallDrawStart(null);
              setWallDrawPreview(null);
            } else {
              handleDeselect();
            }
            return;
          case 'Delete': case 'Backspace':
            e.preventDefault();
            deleteSelected();
            return;
        }
      }

      // Undo: Ctrl/Cmd+Z
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      }
      // Redo: Ctrl/Cmd+Shift+Z
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        redo();
      }
      // Redo: Ctrl/Cmd+Y
      if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        redo();
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [undo, redo, deleteSelected, handleDeselect, wallDrawStart]);

  // Clear wall drawing state when switching tools
  useEffect(() => {
    if (activeTool !== 'wall') {
      setWallDrawStart(null);
      setWallDrawPreview(null);
    }
  }, [activeTool]);

  // Zoom handler
  const handleWheel = useCallback((e) => {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;

    const pointer = stage.getPointerPosition();
    const oldScale = stage.scaleX();
    const scaleBy = 1.08;
    const newScale = e.evt.deltaY < 0 ? oldScale * scaleBy : oldScale / scaleBy;
    const clamped = Math.max(0.1, Math.min(200, newScale));

    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };

    setStageScale(clamped);
    setStagePosition({
      x: pointer.x - mousePointTo.x * clamped,
      y: pointer.y - mousePointTo.y * clamped,
    });
  }, []);

  const handleStageDragEnd = useCallback((e) => {
    setStagePosition({ x: e.target.x(), y: e.target.y() });
  }, []);

  // Canvas cursor
  const canvasCursor = useMemo(() => {
    if (activeTool === 'wall') return 'crosshair';
    if (activeTool === 'door' || activeTool === 'window') return 'copy';
    if (activeTool === 'room') return 'pointer';
    if (activeTool === 'measure') return 'crosshair';
    return 'grab';
  }, [activeTool]);

  return (
    <div className="floorplan-editor">
      {/* Left toolbar */}
      <EditorToolbar
        activeTool={activeTool}
        onToolChange={setActiveTool}
        onUndo={undo}
        onRedo={redo}
        canUndo={historyIndex > 0}
        canRedo={historyIndex < editHistory.length - 1}
        showDimensions={showDimensions}
        onToggleDimensions={() => setShowDimensions((v) => !v)}
      />

      {/* Center canvas */}
      <div
        className="floorplan-canvas"
        ref={containerRef}
        style={{ cursor: canvasCursor }}
      >
        <Stage
          ref={stageRef}
          width={stageSize.width}
          height={stageSize.height}
          scaleX={stageScale}
          scaleY={stageScale}
          x={stagePosition.x}
          y={stagePosition.y}
          draggable={activeTool === 'select' && !selectedElementId}
          onWheel={handleWheel}
          onDragEnd={handleStageDragEnd}
          onClick={handleStageClick}
          onTap={handleStageClick}
          onMouseMove={handleStageMouseMove}
        >
          <Layer>
            <RoomLayer
              rooms={currentFloor?.rooms}
              selectedId={selectedElementId}
              onSelect={handleSelectRoom}
              scale={stageScale}
              complianceResult={complianceResult}
              activeTool={activeTool}
            />
            <WallLayer
              walls={currentFloor?.walls}
              selectedId={selectedElementType === 'wall' ? selectedElementId : null}
              onSelect={handleSelectWall}
              scale={stageScale}
              activeTool={activeTool}
              onWallEndpointDrag={handleWallEndpointDrag}
            />
            <OpeningLayer
              openings={currentFloor?.openings}
              walls={currentFloor?.walls}
              selectedId={selectedElementType === 'opening' ? selectedElementId : null}
              onSelect={handleSelectOpening}
              scale={stageScale}
              onOpeningDrag={handleOpeningDrag}
            />
            <DimensionLayer
              walls={currentFloor?.walls}
              rooms={currentFloor?.rooms}
              scale={stageScale}
              showDimensions={showDimensions}
            />
            <ComplianceBadgeLayer
              complianceResult={complianceResult}
              rooms={currentFloor?.rooms}
              walls={currentFloor?.walls}
              openings={currentFloor?.openings}
              scale={stageScale}
              selectedElementId={selectedElementId}
              onBadgeClick={(rule) => {
                if (rule.element_id) {
                  setSelectedElementId(rule.element_id);
                  setSelectedElementType(rule.element_type || null);
                }
              }}
            />

            {/* Wall drawing preview line */}
            {wallDrawStart && wallDrawPreview && (
              <>
                <Line
                  points={[wallDrawStart[0], wallDrawStart[1], wallDrawPreview[0], wallDrawPreview[1]]}
                  stroke="#c8a55c"
                  strokeWidth={2 / stageScale}
                  dash={[6 / stageScale, 4 / stageScale]}
                  listening={false}
                />
                <Circle
                  x={wallDrawStart[0]}
                  y={wallDrawStart[1]}
                  radius={4 / stageScale}
                  fill="#c8a55c"
                  listening={false}
                />
                <Circle
                  x={wallDrawPreview[0]}
                  y={wallDrawPreview[1]}
                  radius={3 / stageScale}
                  fill="#c8a55c"
                  opacity={0.6}
                  listening={false}
                />
              </>
            )}
          </Layer>
        </Stage>

        {/* Scale calibration modal */}
        {!scaleCalibrated && (
          <ScaleCalibration
            floorPlans={normalizedPlans}
            onCalibrate={(scaleData) => {
              setScaleCalibrated(true);
              if (normalizedPlans) {
                const updated = { ...normalizedPlans, scale: scaleData };
                pushChange(updated);
              }
            }}
            onSkip={() => setScaleCalibrated(true)}
          />
        )}

        {/* Room type popover */}
        {roomTypePopover && (
          <RoomTypeSelector
            currentType={roomTypePopover.currentType}
            position={roomTypePopover.position}
            onTypeChange={handleRoomTypeChange}
          />
        )}

        {/* Wall properties panel */}
        {selectedWall && (
          <WallProperties
            wall={selectedWall}
            onWallUpdate={handleWallUpdate}
            onWallDelete={handleWallDelete}
          />
        )}
      </div>

      {/* Right compliance panel */}
      <CompliancePanel
        complianceResult={complianceResult}
        selectedElementId={selectedElementId}
        onRuleClick={(elementId) => {
          setSelectedElementId(elementId);
          setSelectedElementType(null);
        }}
        loading={complianceLoading}
      />
    </div>
  );
}
