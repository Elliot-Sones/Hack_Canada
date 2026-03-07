import { useMemo } from 'react';
import * as THREE from 'three';

const ROOM_COLORS = {
  living: '#4a7c59',
  bedroom: '#4a6b8a',
  kitchen: '#8a7553',
  bathroom: '#4a8a7c',
  hallway: '#666666',
  dining: '#7c6b4a',
  storage: '#5a5a5a',
  utility: '#5a6b5a',
  balcony: '#6b8a6b',
  garage: '#4a4a4a',
  office: '#6b6b8a',
  other: '#777777',
};

const WALL_COLOR = '#333333';
const WALL_HEIGHT = 2.8;
const FLOOR_Y_SPACING = 3.5;

function RoomMesh({ room, yOffset, isSelected, onClick }) {
  const geometry = useMemo(() => {
    if (!room.polygon || room.polygon.length < 3) return null;
    const shape = new THREE.Shape();
    shape.moveTo(room.polygon[0][0], room.polygon[0][1]);
    for (let i = 1; i < room.polygon.length; i++) {
      shape.lineTo(room.polygon[i][0], room.polygon[i][1]);
    }
    shape.closePath();
    const geo = new THREE.ExtrudeGeometry(shape, { depth: 0.15, bevelEnabled: false });
    geo.rotateX(-Math.PI / 2);
    geo.translate(0, yOffset, 0);
    return geo;
  }, [room.polygon, yOffset]);

  if (!geometry) return null;

  const color = ROOM_COLORS[room.type] || ROOM_COLORS.other;

  return (
    <mesh
      geometry={geometry}
      onClick={(e) => { e.stopPropagation(); onClick?.(room); }}
      castShadow
      receiveShadow
    >
      <meshStandardMaterial
        color={color}
        roughness={0.7}
        metalness={0.1}
        emissive={isSelected ? '#c8a55c' : '#000000'}
        emissiveIntensity={isSelected ? 0.4 : 0}
      />
    </mesh>
  );
}

function WallMesh({ wall, yOffset }) {
  const geometry = useMemo(() => {
    const dx = wall.end[0] - wall.start[0];
    const dy = wall.end[1] - wall.start[1];
    const length = Math.sqrt(dx * dx + dy * dy);
    if (length < 0.01) return null;

    const thickness = wall.thickness_m || 0.2;
    const geo = new THREE.BoxGeometry(length, WALL_HEIGHT, thickness);

    const cx = (wall.start[0] + wall.end[0]) / 2;
    const cz = (wall.start[1] + wall.end[1]) / 2;
    const angle = Math.atan2(dy, dx);

    const matrix = new THREE.Matrix4();
    matrix.makeRotationY(-angle);
    matrix.setPosition(cx, yOffset + WALL_HEIGHT / 2, cz);
    geo.applyMatrix4(matrix);

    return geo;
  }, [wall, yOffset]);

  if (!geometry) return null;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial color={WALL_COLOR} roughness={0.8} metalness={0.05} />
    </mesh>
  );
}

export default function FloorPlanView({ floorPlans, activeFloor, selectedRoom, onRoomClick }) {
  if (!floorPlans?.floor_plans?.length) return null;

  const floors = activeFloor != null
    ? floorPlans.floor_plans.filter((f) => f.floor_number === activeFloor)
    : floorPlans.floor_plans;

  return (
    <group>
      {floors.map((floor) => {
        const yOffset = floor.floor_number * FLOOR_Y_SPACING;
        return (
          <group key={floor.floor_number}>
            {/* Floor slab */}
            <mesh position={[0, yOffset - 0.05, 0]} receiveShadow>
              <boxGeometry args={[100, 0.1, 100]} />
              <meshStandardMaterial color="#222222" roughness={1} transparent opacity={0.3} />
            </mesh>

            {/* Rooms */}
            {floor.rooms?.map((room, i) => (
              <RoomMesh
                key={`room-${floor.floor_number}-${i}`}
                room={room}
                yOffset={yOffset}
                isSelected={selectedRoom?.name === room.name && selectedRoom?.floor === floor.floor_number}
                onClick={(r) => onRoomClick?.({ ...r, floor: floor.floor_number })}
              />
            ))}

            {/* Walls */}
            {floor.walls?.map((wall, i) => (
              <WallMesh
                key={`wall-${floor.floor_number}-${i}`}
                wall={wall}
                yOffset={yOffset}
              />
            ))}
          </group>
        );
      })}
    </group>
  );
}
