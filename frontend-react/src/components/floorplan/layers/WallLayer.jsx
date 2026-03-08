import { useMemo } from 'react';
import { Group, Rect, Circle } from 'react-konva';
import { wallToRect, snapToGrid, snapToEndpoint } from '../../../lib/wallGeometry.js';

const GOLD = '#c8a55c';
const HANDLE_RADIUS_BASE = 5;

function wallFill(wall) {
  if (wall.load_bearing === 'yes') return '#8B4513';
  return wall.type === 'exterior' ? '#333333' : '#555555';
}

function wallDash(wall, scale) {
  if (wall.load_bearing === 'yes') return [8 / scale, 4 / scale];
  if (wall.load_bearing === 'unknown') return [3 / scale, 3 / scale];
  return undefined;
}

export default function WallLayer({
  walls,
  selectedId,
  onSelect,
  scale = 1,
  activeTool,
  onWallEndpointDrag,
}) {
  const wallRects = useMemo(() => {
    if (!walls) return [];
    return walls.map((wall) => {
      const { cx, cy, length, angle, thickness } = wallToRect(wall);
      const logicalThickness = wall.type === 'exterior' ? 8 / scale : 4 / scale;
      const displayThickness = Math.max(logicalThickness, thickness);
      return { wall, cx, cy, length, angle, displayThickness };
    });
  }, [walls, scale]);

  if (!walls || walls.length === 0) return <Group />;

  // Walls should be clickable for select, door, and window tools
  const listening = activeTool === 'select' || activeTool === 'door' || activeTool === 'window';

  return (
    <Group listening={listening}>
      {wallRects.map(({ wall, cx, cy, length, angle, displayThickness }) => {
        const isSelected = wall.id === selectedId;
        const dash = wallDash(wall, scale);

        return (
          <Group key={wall.id}>
            <Rect
              x={cx}
              y={cy}
              width={length}
              height={displayThickness}
              offsetX={length / 2}
              offsetY={displayThickness / 2}
              rotation={(angle * 180) / Math.PI}
              fill={wallFill(wall)}
              stroke={isSelected ? GOLD : undefined}
              strokeWidth={isSelected ? 2 / scale : 0}
              dash={dash}
              onClick={() => onSelect?.(wall.id)}
              onTap={() => onSelect?.(wall.id)}
            />

            {/* Drag handles for selected wall endpoints */}
            {isSelected && activeTool === 'select' && onWallEndpointDrag && (
              <>
                <Circle
                  x={wall.start[0]}
                  y={wall.start[1]}
                  radius={HANDLE_RADIUS_BASE / scale}
                  fill={GOLD}
                  stroke="#1a1a1a"
                  strokeWidth={1 / scale}
                  draggable
                  onDragMove={(e) => {
                    const pos = [e.target.x(), e.target.y()];
                    const snapped = snapToEndpoint(pos, walls);
                    e.target.x(snapped[0]);
                    e.target.y(snapped[1]);
                  }}
                  onDragEnd={(e) => {
                    const pos = [e.target.x(), e.target.y()];
                    onWallEndpointDrag(wall.id, 'start', pos);
                  }}
                />
                <Circle
                  x={wall.end[0]}
                  y={wall.end[1]}
                  radius={HANDLE_RADIUS_BASE / scale}
                  fill={GOLD}
                  stroke="#1a1a1a"
                  strokeWidth={1 / scale}
                  draggable
                  onDragMove={(e) => {
                    const pos = [e.target.x(), e.target.y()];
                    const snapped = snapToEndpoint(pos, walls);
                    e.target.x(snapped[0]);
                    e.target.y(snapped[1]);
                  }}
                  onDragEnd={(e) => {
                    const pos = [e.target.x(), e.target.y()];
                    onWallEndpointDrag(wall.id, 'end', pos);
                  }}
                />
              </>
            )}
          </Group>
        );
      })}
    </Group>
  );
}
