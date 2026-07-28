import React, { useMemo, useRef, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls, Line } from "@react-three/drei";
import * as THREE from "three";
import {
  buildSurfaceArrays,
  valleyPoints,
  randomLine,
  WIDTH,
  DEPTH,
} from "./lib/surface.js";
import { PALETTE } from "./lib/theme.js";

const HOME_POS = new THREE.Vector3(9.5, 7.2, 11.5);
const HOME_TARGET = new THREE.Vector3(0, 1.1, 0);

function Surface({ wireframe }) {
  const geometry = useMemo(() => {
    const { positions, colors, indices } = buildSurfaceArrays();
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    g.setIndex(new THREE.BufferAttribute(indices, 1));
    g.computeVertexNormals();
    return g;
  }, []);

  return (
    <mesh geometry={geometry} castShadow={false}>
      <meshStandardMaterial
        vertexColors
        roughness={0.58}
        metalness={0.06}
        side={THREE.DoubleSide}
        wireframe={wireframe}
        emissiveIntensity={0}
        envMapIntensity={0.4}
      />
    </mesh>
  );
}

// A soft floor grid so the eye has a ground plane to read height against.
function FloorGrid({ colors }) {
  return (
    <gridHelper
      args={[Math.max(WIDTH, DEPTH) + 3, 18, colors[0], colors[1]]}
      position={[0, -0.02, 0]}
    />
  );
}

// The glowing point marker; lerps toward its target every frame for smooth,
// physical-feeling travel even though the underlying index steps discretely.
function Marker({ target, color }) {
  const ref = useRef();
  const light = useRef();
  const goal = useMemo(() => new THREE.Vector3(...target), []);
  useEffect(() => {
    goal.set(target[0], target[1], target[2]);
  }, [target, goal]);
  useFrame((state) => {
    if (!ref.current) return;
    ref.current.position.lerp(goal, 0.16);
    const s = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.06;
    ref.current.scale.setScalar(s);
    if (light.current) light.current.position.copy(ref.current.position);
  });
  return (
    <group>
      <mesh ref={ref} position={target}>
        <sphereGeometry args={[0.17, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={1.5}
          roughness={0.3}
        />
      </mesh>
      <pointLight ref={light} color={color} intensity={6} distance={4} decay={2} />
    </group>
  );
}

// Smoothly flies the camera + orbit target home when `resetToken` changes.
function CameraRig({ controlsRef, resetToken }) {
  const { camera } = useThree();
  const active = useRef(false);
  useEffect(() => {
    if (resetToken > 0) active.current = true;
  }, [resetToken]);
  useFrame(() => {
    if (!active.current || !controlsRef.current) return;
    camera.position.lerp(HOME_POS, 0.1);
    controlsRef.current.target.lerp(HOME_TARGET, 0.1);
    controlsRef.current.update();
    if (camera.position.distanceTo(HOME_POS) < 0.03) active.current = false;
  });
  return null;
}

export default function Scene({
  theme,
  wireframe,
  markerTarget,
  markerColor,
  resetToken,
}) {
  const controls = useRef();
  const pal = PALETTE[theme] || PALETTE.dark;
  return (
    <Canvas
      className="stage-canvas"
      dpr={[1, 2]}
      shadows={false}
      gl={{ antialias: true, alpha: true }}
      camera={{ position: HOME_POS.toArray(), fov: 42, near: 0.1, far: 100 }}
    >
      <color attach="background" args={[pal.bg]} />
      <fog attach="fog" args={[pal.bg, pal.fog[0], pal.fog[1]]} />

      <ambientLight intensity={pal.ambient} />
      <directionalLight position={[8, 14, 6]} intensity={pal.key} color={pal.keyColor} />
      <directionalLight position={[-9, 5, -6]} intensity={pal.rim} color={pal.rimColor} />

      <Surface wireframe={wireframe} />
      <FloorGrid colors={pal.grid} />

      <Line points={valleyPoints} color={pal.teal} lineWidth={3.4} />
      <Line
        points={randomLine}
        color={pal.amber}
        lineWidth={1.6}
        dashed
        dashSize={0.22}
        gapSize={0.16}
      />

      <Marker target={markerTarget} color={markerColor} />

      <OrbitControls
        ref={controls}
        enableDamping
        dampingFactor={0.08}
        rotateSpeed={0.65}
        minDistance={6}
        maxDistance={26}
        maxPolarAngle={Math.PI * 0.49}
        target={HOME_TARGET.toArray()}
      />
      <CameraRig controlsRef={controls} resetToken={resetToken} />
    </Canvas>
  );
}
