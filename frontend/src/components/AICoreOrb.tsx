"use client";

import React, { useRef, useState } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, Torus, MeshDistortMaterial, OrbitControls, Environment, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";
import { useAlchemistOS, OrbState } from "@/lib/WebSocketProvider";

const CoreSphere = ({ state, audioLevel }: { state: OrbState; audioLevel: number }) => {
  const meshRef = useRef<THREE.Mesh>(null);
  
  // Animation parameters based on state
  const targetScale = state === "listening" ? 1.2 + audioLevel : state === "thinking" ? 0.9 : state === "speaking" ? 1.1 + audioLevel : 1;
  const targetSpeed = state === "thinking" ? 5 : state === "executing" ? 3 : 1;
  const targetDistort = state === "thinking" ? 0.8 : state === "speaking" ? 0.4 + audioLevel : 0.2;
  
  useFrame((scene, delta) => {
    if (meshRef.current) {
      // Lerp scale for smooth transitions
      meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1);
      meshRef.current.rotation.y += delta * targetSpeed;
      meshRef.current.rotation.x += delta * (targetSpeed * 0.5);
    }
  });

  return (
    <Sphere ref={meshRef} args={[1.5, 64, 64]}>
      <MeshDistortMaterial
        color="#ff003c"
        emissive="#7a001f"
        emissiveIntensity={state === "listening" || state === "speaking" ? 2 : 1.5}
        wireframe={state === "thinking"}
        distort={targetDistort}
        speed={targetSpeed}
        roughness={0.2}
        metalness={0.8}
      />
    </Sphere>
  );
};

const OuterRings = ({ state }: { state: OrbState }) => {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((_, delta) => {
    if (groupRef.current) {
      const speed = state === "thinking" ? 4 : state === "executing" ? 2 : 0.5;
      groupRef.current.rotation.x += delta * speed;
      groupRef.current.rotation.y += delta * (speed * 1.2);
    }
  });

  return (
    <group ref={groupRef}>
      <Torus args={[2.2, 0.05, 16, 100]} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial color="#ff003c" emissive="#ff003c" emissiveIntensity={2} />
      </Torus>
      <Torus args={[2.5, 0.02, 16, 100]} rotation={[0, Math.PI / 4, 0]}>
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={1} opacity={0.5} transparent />
      </Torus>
      <Torus args={[2.8, 0.03, 16, 100]} rotation={[0, 0, Math.PI / 3]}>
        <meshStandardMaterial color="#ff003c" emissive="#7a001f" emissiveIntensity={2} />
      </Torus>
    </group>
  );
};

const Particles = ({ state, audioLevel }: { state: OrbState; audioLevel: number }) => {
  const pointsRef = useRef<THREE.Points>(null);

  const [positions] = useState(() => {
    const count = 500;
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      // Create a sphere distribution
      const r = 3 + Math.random() * 2;
      const theta = 2 * Math.PI * Math.random();
      const phi = Math.acos(2 * Math.random() - 1);
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  });

  useFrame((scene, delta) => {
    if (pointsRef.current) {
      const speed = state === "thinking" ? 1.5 : state === "executing" ? 1 : 0.2;
      pointsRef.current.rotation.y += delta * speed;
      pointsRef.current.rotation.z += delta * (speed * 0.5);
      
      const scale = state === "speaking" ? 1 + (audioLevel * 0.5) : 1;
      pointsRef.current.scale.lerp(new THREE.Vector3(scale, scale, scale), 0.1);
    }
  });

  return (
    <Points ref={pointsRef} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#ff003c"
        size={0.05}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
};

export const AICoreOrb = ({ audioLevel = 0 }: { audioLevel?: number }) => {
  const { state } = useAlchemistOS();

  return (
    <div className="w-full h-full relative">
      {/* Background glow behind canvas */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-crimson-500 rounded-full blur-[100px] opacity-30 pointer-events-none" />
      
      <Canvas camera={{ position: [0, 0, 8], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={2} color="#ff003c" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#ffffff" />
        
        <CoreSphere state={state.orbState} audioLevel={audioLevel} />
        <OuterRings state={state.orbState} />
        <Particles state={state.orbState} audioLevel={audioLevel} />
        
        <OrbitControls enableZoom={false} enablePan={false} autoRotate={state.orbState === "idle"} autoRotateSpeed={0.5} />
        <Environment preset="city" />
      </Canvas>
    </div>
  );
};
