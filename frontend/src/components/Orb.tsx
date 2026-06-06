"use client";

import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Sphere, MeshDistortMaterial } from "@react-three/drei";
import * as THREE from "three";

interface OrbProps {
  status: "idle" | "listening" | "thinking" | "speaking";
}

function AnimatedSphere({ status }: OrbProps) {
  const sphereRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (sphereRef.current) {
      sphereRef.current.rotation.x = clock.getElapsedTime() * 0.2;
      sphereRef.current.rotation.y = clock.getElapsedTime() * 0.3;
      
      if (status === "speaking") {
        const scale = 1 + Math.sin(clock.getElapsedTime() * 10) * 0.1;
        sphereRef.current.scale.set(scale, scale, scale);
      } else {
        sphereRef.current.scale.set(1, 1, 1);
      }
    }
  });

  const getMaterialProps = () => {
    switch (status) {
      case "listening":
        return { color: "#00ff88", distort: 0.6, speed: 4 };
      case "thinking":
        return { color: "#0088ff", distort: 0.8, speed: 2 };
      case "speaking":
        return { color: "#ff0088", distort: 0.5, speed: 6 };
      case "idle":
      default:
        return { color: "#4444ff", distort: 0.3, speed: 1 };
    }
  };

  const { color, distort, speed } = getMaterialProps();

  return (
    <Sphere ref={sphereRef} args={[1, 64, 64]}>
      <MeshDistortMaterial
        color={color}
        envMapIntensity={1}
        clearcoat={1}
        clearcoatRoughness={0.1}
        metalness={0.8}
        roughness={0.2}
        distort={distort}
        speed={speed}
      />
    </Sphere>
  );
}

export default function Orb({ status }: OrbProps) {
  return (
    <div className="w-64 h-64">
      <Canvas camera={{ position: [0, 0, 3] }}>
        <ambientLight intensity={1.5} />
        <directionalLight position={[2, 2, 2]} intensity={2} />
        <AnimatedSphere status={status} />
      </Canvas>
    </div>
  );
}
