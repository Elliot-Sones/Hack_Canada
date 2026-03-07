import { useRef, useMemo, Suspense } from 'react';
import { createPortal } from 'react-dom';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';
import { extractFootprint, shrinkPolygon } from '../lib/buildingGeometry.js';
import '../ModelViewer.css';

const DEFAULT_PARAMS = {
  storeys: 10,
  podium_storeys: 0,
  height_m: 35,
  setback_m: 0,
  typology: 'midrise',
  footprint_coverage: 0.6,
};

// ─── Camera reset helper ───────────────────────────────────────────────────────

function CameraResetButton({ controlsRef }) {
  const { camera } = useThree();
  const handleReset = () => {
    camera.position.set(0, 40, 80);
    camera.lookAt(0, 0, 0);
    if (controlsRef.current) {
      controlsRef.current.target.set(0, 0, 0);
      controlsRef.current.update();
    }
  };
  return (
    <button className="model-ctrl-btn" onClick={handleReset} title="Reset camera">
      ↺ Reset
    </button>
  );
}

// ─── Building mesh ─────────────────────────────────────────────────────────────

function BuildingMesh({ parcelGeoJSON, params }) {
  const p = params || DEFAULT_PARAMS;

  const { podiumGeo, towerGeo } = useMemo(() => {
    const footprint = extractFootprint(parcelGeoJSON);

    // Scale footprint by coverage factor
    const scaledFootprint = footprint.map(([x, z]) => [
      x * (p.footprint_coverage ?? 0.6),
      z * (p.footprint_coverage ?? 0.6),
    ]);

    const podiumH = (p.podium_storeys || 0) * 4.5;
    const totalH = p.height_m || 35;
    const towerH = Math.max(0, totalH - podiumH);

    // Build podium shape
    const podShape = new THREE.Shape();
    podShape.moveTo(scaledFootprint[0][0], scaledFootprint[0][1]);
    for (let i = 1; i < scaledFootprint.length; i++) {
      podShape.lineTo(scaledFootprint[i][0], scaledFootprint[i][1]);
    }
    podShape.closePath();

    const podiumGeo = new THREE.ExtrudeGeometry(podShape, {
      depth: Math.max(podiumH, 0.5),
      bevelEnabled: false,
    });
    // Rotate so extrusion goes up (Y axis)
    podiumGeo.rotateX(-Math.PI / 2);

    let towerGeo = null;
    if (towerH > 0.5) {
      const setback = p.setback_m || 0;
      const towerFP = shrinkPolygon(scaledFootprint, setback);

      const towerShape = new THREE.Shape();
      towerShape.moveTo(towerFP[0][0], towerFP[0][1]);
      for (let i = 1; i < towerFP.length; i++) {
        towerShape.lineTo(towerFP[i][0], towerFP[i][1]);
      }
      towerShape.closePath();

      towerGeo = new THREE.ExtrudeGeometry(towerShape, {
        depth: towerH,
        bevelEnabled: false,
      });
      towerGeo.rotateX(-Math.PI / 2);
      towerGeo.translate(0, podiumH, 0);
    }

    return { podiumGeo, towerGeo };
  }, [parcelGeoJSON, p]);

  return (
    <group>
      {/* Podium */}
      <mesh geometry={podiumGeo} castShadow receiveShadow>
        <meshStandardMaterial color="#c8a55c" roughness={0.6} metalness={0.1} />
      </mesh>

      {/* Tower */}
      {towerGeo && (
        <mesh geometry={towerGeo} castShadow receiveShadow>
          <meshStandardMaterial color="#d4b87a" roughness={0.5} metalness={0.15} />
        </mesh>
      )}
    </group>
  );
}

// ─── Ground plane ──────────────────────────────────────────────────────────────

function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.05, 0]} receiveShadow>
      <planeGeometry args={[600, 600]} />
      <meshStandardMaterial color="#1a1a1a" roughness={1} />
    </mesh>
  );
}

// ─── Scene wrapper ─────────────────────────────────────────────────────────────

function Scene({ parcelGeoJSON, params, controlsRef }) {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight
        position={[60, 120, 60]}
        intensity={1.2}
        castShadow
        shadow-mapSize-width={1024}
        shadow-mapSize-height={1024}
      />
      <directionalLight position={[-40, 60, -40]} intensity={0.4} />

      <OrbitControls
        ref={controlsRef}
        enablePan={false}
        minDistance={10}
        maxDistance={400}
        maxPolarAngle={Math.PI / 2 - 0.02}
      />

      <Suspense fallback={null}>
        <BuildingMesh parcelGeoJSON={parcelGeoJSON} params={params} />
      </Suspense>

      <Ground />
    </>
  );
}

// ─── Main modal ────────────────────────────────────────────────────────────────

export default function ModelViewer({ isOpen, onClose, parcelGeoJSON, modelParams, isPanelOpen, isSidebarCollapsed, isChatExpanded }) {
  const controlsRef = useRef(null);
  const params = modelParams || DEFAULT_PARAMS;
  const isEmpty = !modelParams;

  if (!isOpen) return null;

  const totalH = Math.round(params.height_m || 0);
  const storeys = params.storeys || 0;

  const closeBtn = createPortal(
    <button
      className="model-close-btn"
      onPointerDown={(e) => { e.stopPropagation(); e.preventDefault(); onClose(); }}
      aria-label="Close model"
      style={{
        position: 'fixed',
        top: 12,
        right: (isPanelOpen ? 380 : 0) + 16,
        zIndex: 99999,
        transition: 'right 0.3s ease',
      }}
    >✕</button>,
    document.body
  );

  const sidebarW = isSidebarCollapsed ? 52 : 160;
  const panelW = isPanelOpen ? 380 : 0;
  const chatH = isChatExpanded ? 328 : 48;

  return (
    <>
      {closeBtn}
      {/* Full-screen dark backdrop — covers the map completely */}
      <div className="model-overlay" />
      {/* Canvas sized to the visible gap between panels */}
      <div
        className="model-canvas-area"
        style={{
          position: 'fixed',
          top: 0,
          left: sidebarW,
          right: panelW,
          bottom: chatH,
          zIndex: 6,
          transition: 'left 0.3s ease, right 0.3s ease, bottom 0.3s ease',
        }}
      >
        <Canvas
          camera={{ position: [0, 40, 80], fov: 45 }}
          shadows
          style={{ width: '100%', height: '100%', background: 'transparent' }}
          eventPrefix="client"
        >
          <Scene parcelGeoJSON={parcelGeoJSON} params={params} controlsRef={controlsRef} />
        </Canvas>
      </div>
      {/* Controls bar at the bottom of the visible area */}
      <div
        className="model-controls"
        style={{
          position: 'fixed',
          left: sidebarW,
          right: panelW,
          bottom: chatH,
          zIndex: 7,
          transition: 'left 0.3s ease, right 0.3s ease, bottom 0.3s ease',
        }}
      >
        <button
          className="model-ctrl-btn"
          onClick={() => {
            if (controlsRef.current) {
              controlsRef.current.object.position.set(0, 40, 80);
              controlsRef.current.target.set(0, 0, 0);
              controlsRef.current.update();
            }
          }}
          title="Reset camera"
        >
          ↺ Reset
        </button>
        <span className="model-info">
          {storeys} storeys · {totalH}m
          {params.typology ? ` · ${params.typology.replace(/_/g, ' ')}` : ''}
        </span>
      </div>
    </>
  );
}
