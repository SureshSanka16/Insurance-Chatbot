
import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame, ThreeElements } from '@react-three/fiber';
import { Sphere, OrbitControls, Points, PointMaterial, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';

// Standard JSX elements are already provided by @types/react.
// React Three Fiber elements are handled by the library's internal type extensions.

function MovingLight() {
    const light = useRef<THREE.PointLight>(null!);
    useFrame((state) => {
        light.current.position.x = state.pointer.x * 6;
        light.current.position.y = state.pointer.y * 6;
    });

    return (
        <pointLight 
            ref={light} 
            position={[0, 0, 3]} 
            intensity={10} 
            color="#F97316" 
            distance={15} 
            decay={2}
        />
    );
}

function Particles({ count = 2000 }) {
  const points = useRef<THREE.Points>(null!);
  
  const particlesPosition = useMemo(() => {
    const positions = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = THREE.MathUtils.randFloatSpread(360);
      const phi = THREE.MathUtils.randFloatSpread(360);
      const radius = 2 + Math.random() * 2;
      
      const x = radius * Math.sin(theta) * Math.cos(phi);
      const y = radius * Math.sin(theta) * Math.sin(phi);
      const z = radius * Math.cos(theta);
      
      positions.set([x, y, z], i * 3);
    }
    return positions;
  }, [count]);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    points.current.rotation.y = time * 0.05;
    points.current.rotation.x = time * 0.02;
  });

  return (
    <Points ref={points} positions={particlesPosition} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#F97316"
        size={0.03}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.6}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  );
}

function AnimatedBlob() {
    const meshRef = useRef<THREE.Mesh>(null!);
    useFrame((state) => {
        const time = state.clock.getElapsedTime();
        meshRef.current.rotation.x = time * 0.1;
        meshRef.current.rotation.y = time * 0.15;
    });

    return (
        <Sphere args={[1.2, 64, 64]} ref={meshRef}>
            <MeshDistortMaterial 
                color="#F97316" 
                speed={2} 
                distort={0.4} 
                radius={1}
                wireframe
                transparent
                opacity={0.15}
            />
        </Sphere>
    )
}

export const ThreeScene = () => {
  return (
    <div className="w-full h-full min-h-[300px]">
      <Canvas camera={{ position: [0, 0, 5], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={2} color="#F97316" />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#3B82F6" />
        
        <MovingLight />
        <Particles count={3000} />
        <AnimatedBlob />
        
        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
      </Canvas>
    </div>
  );
};